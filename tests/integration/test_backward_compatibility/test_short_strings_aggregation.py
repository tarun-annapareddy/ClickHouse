import pytest

from helpers.cluster import ClickHouseCluster, CLICKHOUSE_CI_MIN_TESTED_VERSION

cluster = ClickHouseCluster(__file__)
node1 = cluster.add_instance(
    "node1",
    with_zookeeper=False,
    image="clickhouse/clickhouse-server",
    tag=CLICKHOUSE_CI_MIN_TESTED_VERSION,
    stay_alive=True,
    with_installed_binary=True,
    allow_analyzer=False,
)
node2 = cluster.add_instance(
    "node2",
    with_zookeeper=False,
    image="clickhouse/clickhouse-server",
    tag=CLICKHOUSE_CI_MIN_TESTED_VERSION,
    stay_alive=True,
    with_installed_binary=True,
    allow_analyzer=False,
)
node3 = cluster.add_instance("node3", with_zookeeper=False, allow_analyzer=False)


@pytest.fixture(scope="module")
def start_cluster():
    try:
        cluster.start()
        yield cluster

    finally:
        cluster.shutdown()


def test_backward_compatability(start_cluster):
    node1.query("create table tab (s String) engine = MergeTree order by s")
    node2.query("create table tab (s String) engine = MergeTree order by s")
    node1.query("insert into tab select number from numbers(50)")
    node2.query("insert into tab select number from numbers(1000000)")
    res = node3.query(
        "select s, count() from remote('node{1,2}', default, tab) group by s order by toUInt64(s) limit 50"
    )
    print(res)
    assert res == "".join("{}\t2\n".format(i) for i in range(50))
    node1.query("drop table tab")
    node2.query("drop table tab")
