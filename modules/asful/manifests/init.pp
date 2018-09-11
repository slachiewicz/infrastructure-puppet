#/etc/puppet/modules/asful/manifests/init.pp

class asful (
  $nodename       = 'ul1-eu-central',
  $nodeip         = '10.91.64.150',
  $clusterlist    = '[]',
  $minimum_master_nodes = 2

){
  include 'elasticsearch'

  File<|title == '/etc/elasticsearch/asful/elasticsearch.asful.yml'|> {
      ensure => file,
      mode   => '0755',
      owner  => 'elasticsearch',
      group  => 'elasticsearch',
      content => template('asful/yaml.erb'),
    }
    
  file {
    '/usr/local/etc/webstats.py':
      ensure => file,
      mode   => '0755',
      owner  => 'www-data',
      group  => 'www-data',
      source => 'puppet:///modules/asful/webstats.py';
    '/var/www/snappy/domains.txt':
      ensure => file,
      mode   => '0755',
      owner  => 'www-data',
      group  => 'www-data',
      source => 'puppet:///modules/asful/webstats-domains.txt';
  }
  
  cron {
    'run-webstats':
      user        => 'www-data',
      minute      => '0',
      hour        => '*/4',
      command     => "cd /usr/local/etc && python webstats.py > /dev/null",
      environment => [
        'PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin',
        'SHELL=/bin/sh'
      ];
  }
}
