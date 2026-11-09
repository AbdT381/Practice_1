import os
import tempfile
import unittest

from src.emulator import VFS, Emulator


class TestVFS(unittest.TestCase):
    def test_default(self):
        vfs = VFS.default()
        self.assertIn("home", vfs.list_dir("/"))

    def test_from_csv(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("/,dir,\n")
            f.write("/a.txt,file,Hi\n")
            f.write("/d,dir,\n")
            f.write("/d/b.txt,file,Bye\n")
            name = f.name
        try:
            vfs = VFS.from_csv(name)
            self.assertEqual(vfs.list_dir("/"), ["a.txt", "d"])
            self.assertEqual(vfs.list_dir("/d"), ["b.txt"])
        finally:
            os.unlink(name)

    def test_cd(self):
        vfs = VFS.default()
        vfs.change_dir("/home/user")
        self.assertEqual(vfs.cwd, "/home/user")
        self.assertEqual(vfs.list_dir("."), ["file.txt"])


class TestEmulator(unittest.TestCase):
    def setUp(self):
        self.vfs = VFS.default()
        self.emu = Emulator(self.vfs)

    def test_expand_vars(self):
        os.environ["TEST_VAR"] = "value"
        self.assertEqual(self.emu.expand_vars("$TEST_VAR"), "value")
        self.assertEqual(self.emu.expand_vars("${TEST_VAR}"), "value")

    def test_ls(self):
        rc = self.emu.cmd_ls([])
        self.assertEqual(rc, 0)

    def test_cd_error(self):
        rc = self.emu.cmd_cd(["/nonexistent"])
        self.assertEqual(rc, 1)

    def test_unknown_command(self):
        rc = self.emu.dispatch("unknown_cmd")
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
