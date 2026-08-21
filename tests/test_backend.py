import pytest
from src.backend.models import MessageStore

def test_message_store_initialization():
    store = MessageStore()
    assert store.count() >= 3
    channels = store.get_channels()
    assert "general" in channels
    assert "distributed-systems" in channels

def test_message_store_add_and_retrieve():
    store = MessageStore()
    msg = store.add_message(sender="TestUser", content="Testing 123", channel="random")
    assert msg["id"] is not None
    assert msg["sender"] == "TestUser"
    assert msg["content"] == "Testing 123"
    assert msg["channel"] == "random"

    retrieved = store.get_message_by_id(msg["id"])
    assert retrieved is not None
    assert retrieved["content"] == "Testing 123"

def test_message_store_channel_filtering():
    store = MessageStore()
    store.add_message(sender="Alice", content="General update", channel="general")
    store.add_message(sender="Bob", content="Announce 1", channel="announcements")

    gen_msgs = store.get_messages(channel="general")
    for m in gen_msgs:
        assert m["channel"] == "general"

    ann_msgs = store.get_messages(channel="announcements")
    for m in ann_msgs:
        assert m["channel"] == "announcements"
