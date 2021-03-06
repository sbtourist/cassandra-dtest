import time

from assertions import assert_length_equal
from dtest import Tester


class TestRangeGhosts(Tester):

    def ghosts_test(self):
        """ Check range ghost are correctly removed by the system """
        cluster = self.cluster
        cluster.populate(1).start()
        [node1] = cluster.nodelist()

        time.sleep(.5)
        session = self.cql_connection(node1)
        self.create_ks(session, 'ks', 1)
        self.create_cf(session, 'cf', gc_grace=0, columns={'c': 'text'})

        rows = 1000

        for i in xrange(0, rows):
            session.execute("UPDATE cf SET c = 'value' WHERE key = 'k%i'" % i)

        res = list(session.execute("SELECT * FROM cf LIMIT 10000"))
        assert_length_equal(res, rows)

        node1.flush()

        for i in xrange(0, rows / 2):
            session.execute("DELETE FROM cf WHERE key = 'k%i'" % i)

        res = list(session.execute("SELECT * FROM cf LIMIT 10000"))
        # no ghosts in 1.2+
        assert_length_equal(res, rows / 2)

        node1.flush()
        time.sleep(1)  # make sure tombstones are collected
        node1.compact()

        res = list(session.execute("SELECT * FROM cf LIMIT 10000"))
        assert_length_equal(res, rows / 2)
