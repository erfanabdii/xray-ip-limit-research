"""Offline state-model tests, NOT a coordinator implementation or daemon.

Models central ownership and explicit close acknowledgment. No network, disk
database, timers, real accounts, deployment code, or Xray integration.
"""
import copy
import itertools
import unittest
import uuid

class OwnershipModel:
    def __init__(self, caps, saved=None):
        self.caps = caps
        self.owners = copy.deepcopy(saved or {})
        self.serial = 1000
        self.epoch = uuid.uuid4().hex

    def reserve(self, account, ip, node):
        owners = self.owners.setdefault(account, {})
        if ip not in owners and len(owners) >= self.caps[account]:
            return None
        nodes = owners.setdefault(ip, {})
        if node not in nodes:
            self.serial += 1
            nodes[node] = f'fixture-token-{self.epoch}-{self.serial}'
        return nodes[node]

    def close_ack(self, account, ip, node, token):
        # Called only AFTER that node has stopped all associated flows.
        owners = self.owners.get(account, {})
        nodes = owners.get(ip, {})
        if nodes.get(node) != token:
            return False
        del nodes[node]
        if not nodes:
            owners.pop(ip, None)
        return True

    def heartbeat_missing(self, node):
        # Liveness loss blocks new grants on that node, but is not proof its
        # already-dispatched flows are stopped. Never reclaim its count here.
        return None

    def count(self, account):
        return len(self.owners.get(account, {}))

class CoordinationDiagnostics(unittest.TestCase):
    def test_both_atomic_arrival_orders_have_one_winner(self):
        for order in itertools.permutations([('A', 'NODE-A'), ('B', 'NODE-B')]):
            model = OwnershipModel({'fixture': 1})
            grants = [model.reserve('fixture', ip, node) for ip, node in order]
            self.assertEqual(sum(x is not None for x in grants), 1)
            self.assertEqual(model.count('fixture'), 1)

    def test_same_ip_on_two_nodes_counts_once_and_last_close_releases(self):
        model = OwnershipModel({'fixture': 1})
        usa = model.reserve('fixture', 'A', 'NODE-A')
        pol = model.reserve('fixture', 'A', 'NODE-B')
        self.assertEqual(model.count('fixture'), 1)
        self.assertTrue(model.close_ack('fixture', 'A', 'NODE-A', usa))
        self.assertIsNone(model.reserve('fixture', 'B', 'NODE-A'))
        self.assertTrue(model.close_ack('fixture', 'A', 'NODE-B', pol))
        self.assertIsNotNone(model.reserve('fixture', 'B', 'NODE-A'))

    def test_other_account_same_ip_is_independent(self):
        model = OwnershipModel({'first': 1, 'second': 1})
        self.assertIsNotNone(model.reserve('first', 'A', 'NODE-A'))
        self.assertIsNotNone(model.reserve('second', 'A', 'NODE-B'))
        self.assertIsNone(model.reserve('first', 'B', 'NODE-B'))

    def test_missing_heartbeat_does_not_reclaim_live_unknown_node(self):
        model = OwnershipModel({'fixture': 1})
        model.reserve('fixture', 'A', 'NODE-A')
        model.heartbeat_missing('NODE-A')
        self.assertIsNone(model.reserve('fixture', 'B', 'NODE-B'))
        self.assertEqual(model.count('fixture'), 1)

    def test_diagnostic_naive_expiry_can_exceed_real_active_limit(self):
        model = OwnershipModel({'fixture': 1})
        model.reserve('fixture', 'A', 'NODE-A')
        real_active = {'A'}  # Partition does not stop the old tunnel.
        model.owners.clear()  # Counterexample: reclaim by TTL alone.
        self.assertIsNotNone(model.reserve('fixture', 'B', 'NODE-B'))
        real_active.add('B')
        self.assertGreater(len(real_active), 1)

    def test_old_release_cannot_delete_reacquired_generation(self):
        model = OwnershipModel({'fixture': 1})
        old = model.reserve('fixture', 'A', 'NODE-A')
        self.assertTrue(model.close_ack('fixture', 'A', 'NODE-A', old))
        fresh = model.reserve('fixture', 'A', 'NODE-A')
        self.assertNotEqual(old, fresh)
        self.assertFalse(model.close_ack('fixture', 'A', 'NODE-A', old))
        self.assertIsNone(model.reserve('fixture', 'B', 'NODE-B'))

    def test_restart_restoring_ownership_keeps_conflicting_ip_denied(self):
        model = OwnershipModel({'fixture': 1})
        model.reserve('fixture', 'A', 'NODE-A')
        restarted = OwnershipModel({'fixture': 1}, saved=model.owners)
        # Real implementation also needs durable token generation/session epoch.
        self.assertIsNone(restarted.reserve('fixture', 'B', 'NODE-B'))

    def test_diagnostic_two_uncoordinated_leaders_can_both_admit(self):
        usa_leader = OwnershipModel({'fixture': 1})
        pol_leader = OwnershipModel({'fixture': 1})
        self.assertIsNotNone(usa_leader.reserve('fixture', 'A', 'NODE-A'))
        self.assertIsNotNone(pol_leader.reserve('fixture', 'B', 'NODE-B'))
        self.assertEqual(len({'A', 'B'}), 2)

    def test_restart_old_release_cannot_match_a_new_permit(self):
        model = OwnershipModel({'fixture': 1})
        old = model.reserve('fixture', 'A', 'NODE-A')
        restarted = OwnershipModel({'fixture': 1}, saved=model.owners)
        self.assertTrue(restarted.close_ack('fixture', 'A', 'NODE-A', old))
        fresh = restarted.reserve('fixture', 'A', 'NODE-A')
        self.assertNotEqual(old, fresh)
        self.assertFalse(restarted.close_ack('fixture', 'A', 'NODE-A', old))

if __name__ == '__main__':
    unittest.main(verbosity=2)
