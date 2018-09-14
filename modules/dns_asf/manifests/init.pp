class dns_asf {

  include bind

  bind::server::conf { '/etc/bind/named.conf':
    recursion           => 'yes',
    directory           => '/var/cache/bind',
    listen_on_addr      => [ 'any' ],
    listen_on_v6_addr   => [ 'any' ],
    forwarders          => [ '140.211.166.140', '140.211.166.141' ],
    allow_query         => [ 'ns_slaves' ],
    allow_transfer      => [ 'ns_slaves' ],
    allow_recursion     => [ 'ns_slaves' ],
    allow_query_cache   => [ 'ns_slaves' ],

    acls => {
      'ns_slaves' => [ 
        '127.0.0.1',
        '140.211.11.9',

        '8.23.224.170',
        '52.8.156.211',
        '64.235.248.120',
        '192.87.36.2',

        '140.211.166.126',
        '140.211.15.61',
      ],
    },

    zones => {
      'apache.org' => [
        'type master',
        'file /etc/namedb/zones/apache.org',
        'notify yes',
      ],
      'apachecon.com' => [
        'type master',
        'file /etc/namedb/zones/apachecon.com',
        'notify yes',
      ],
      'openoffice.org' => [
        'type master',
        'file /etc/namedb/zones/openoffice.org',
        'notify yes',
      ],
    }

  }
  
  vcsrepo { "/etc/bind/master":
    ensure   => latest,
    provider => 'svn',
    source   => 'svn path'
    revision => 'master',
    before   => Bind::Server::Conf['/etc/bind/named.conf'],
  }

  exec { "rndc reload":
    command   => "/usr/sbin/rndc reload",
    subscribe => Vcsrepo['/etc/bind/master'],
  }

}
