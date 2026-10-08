"""Exercise source archive reproducibility and download failure propagation."""
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Downloads(unittest.TestCase):
    def setUp(self):
        (ROOT / ".work").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="downloads-test-", dir=ROOT / ".work")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)

    def run_command(self, *args, **kwargs):
        return subprocess.run(args, cwd=self.work, check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, **kwargs).stdout

    def test_git_archive_ignores_caller_umask(self):
        source = self.work / "repository"
        source.mkdir()
        (source / "README").write_text("source fixture\n")
        (source / "run.sh").write_text("#!/bin/sh\nexit 0\n")
        (source / "run.sh").chmod(0o755)
        (source / "link").symlink_to("README")
        self.run_command("git", "init", "-q", str(source))
        self.run_command("git", "-C", str(source), "add", ".")
        self.run_command("git", "-C", str(source), "-c", "user.name=Test",
                         "-c", "user.email=test@example.com", "commit", "-qm", "Fixture")
        revision = self.run_command("git", "-C", str(source), "rev-parse", "HEAD").strip()
        hashes = []
        for mask in (0o022, 0o077):
            case = self.work / str(mask)
            case.mkdir()
            makefile = case / "Makefile"
            makefile.write_text(f"""TMP_DIR:={case}/tmp
DL_DIR:={case}/downloads
TAR:=tar
PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:={source}
PKG_SOURCE_VERSION:={revision}
PKG_SOURCE_SUBDIR:=fixture
PKG_SOURCE:=fixture.tar.gz
PKG_SOURCE_SUBMODULES:=skip
ext=$(lastword $(subst ., ,$(1)))
locked=$(1)
include {ROOT}/include/download.mk
$(eval $(call Download,default))
""")
            self.run_command("make", "--no-print-directory", "-f", str(makefile), "download",
                             umask=mask, env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1",
                                              "GIT_CONFIG_GLOBAL": "/dev/null"})
            archive = case / "downloads/fixture.tar.gz"
            hashes.append(hashlib.sha256(archive.read_bytes()).hexdigest())
            with tarfile.open(archive) as tar:
                self.assertEqual(tar.getmember("fixture/README").mode, 0o644)
                self.assertEqual(tar.getmember("fixture/run.sh").mode, 0o755)
                self.assertEqual(tar.getmember("fixture/link").linkname, "README")
        self.assertEqual(hashes[0], hashes[1])

    def test_download_stops_on_first_failure(self):
        text = (ROOT / "include/toplevel.mk").read_text()
        recipe = re.search(r"^download:.*\n(\t[^\n]+)", text, re.M)[1]
        (self.work / "Makefile").write_text(
            f"DOWNLOAD_DIRS:=first second\nSUBMAKE=$(MAKE) -f child.mk\ndownload:\n{recipe}\n")
        (self.work / "child.mk").write_text(
            "first:\n\t@exit 17\nsecond:\n\t@touch continued\n")
        result = subprocess.run(["make", "--no-print-directory", "download"], cwd=self.work,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.work / "continued").exists())


if __name__ == "__main__":
    unittest.main()
