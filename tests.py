from order import Order
import pytest

def test_order_to_dict():
    order = Order('EURUSD', 100, 'call', 1)
    expected = {
            "asset": "EURUSD",
            "amount": 100,
            "action": "call",
            "duration": 1
    }
    assert order.to_dict() == expected

def test_dict_to_order():
    aorder_dict = {
            "asset": "EURUSD",
            "amount": 100,
            "action": "call",
            "duration": 1
    }
    expected = Order.from_dict(aorder_dict)
    assert aorder_dict['asset'] == expected.asset
    assert aorder_dict['amount'] == expected.amount
    assert aorder_dict['action'] == expected.action
    assert aorder_dict['duration'] == expected.duration