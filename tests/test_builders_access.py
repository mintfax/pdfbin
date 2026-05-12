import pikepdf
import pytest
from generate.builders import access


def test_builds_seven_encrypted_variants(tmp_path):
    records = access.build_all(tmp_path)
    expected = {
        "aes256-owner", "aes256-user", "aes256-both",
        "aes128-owner", "aes128-user",
        "rc4-128-owner", "rc4-40-owner",
    }
    assert {r.id for r in records} == expected


def test_aes256_owner_opens_with_owner_password(tmp_path):
    access.build_all(tmp_path)
    pdf = pikepdf.open(str(tmp_path / "aes256-owner.pdf"), password="ownerpass")
    assert len(pdf.pages) >= 1
    pdf.close()


def test_aes256_user_opens_with_user_password(tmp_path):
    access.build_all(tmp_path)
    pdf = pikepdf.open(str(tmp_path / "aes256-user.pdf"), password="userpass")
    assert len(pdf.pages) >= 1
    pdf.close()


def test_aes256_user_rejects_wrong_password(tmp_path):
    access.build_all(tmp_path)
    with pytest.raises(pikepdf.PasswordError):
        pikepdf.open(str(tmp_path / "aes256-user.pdf"), password="wrong")
