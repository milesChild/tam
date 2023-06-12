import sys
sys.path.append("..")
from util import telegrambot

def test_is_new_cp():
    user = 1
    is_new = telegrambot._is_new(user)

    assert ~is_new, f"user {user} should not be new"

def test_is_new_cp():
    user = 2
    is_new = telegrambot._is_new(user)

    assert is_new, f"user {user} should be new"

def test_generate_user():
    user = 2
    val = telegrambot._generate_random_user(user)

    assert val['counterparty_id']>0, "You didn't generate a random counteraprty id correctly"


