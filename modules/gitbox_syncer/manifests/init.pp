#/etc/puppet/modules/gitbox_syncer/manifests/init.pp

class gitbox_syncer (
  $service_name   = 'gitbox-poller',
  $shell          = '/bin/bash',
  $service_ensure = 'running',
  $username       = 'root',
  $group          = 'root',
)
{

  
  require python
  
  if !defined(Python::Pip['gunicorn']) {
    python::pip {
      'gunicorn' :
        ensure => present;
    }
  }
  if !defined(Python::Pip['netaddr']) {
    python::pip {
      'netaddr' :
        ensure => present;
    }
  }
  if !defined(Python::Pip['asfpy']) {
    python::pip {
      'asfpy' :
        ensure  => present;
    }
  }
  if !defined(Python::Pip['requests']) {
    python::pip {
      'requests' :
        ensure => present;
    }
  }
  if !defined(Python::Pip['pyyaml']) {
    python::pip {
      'pyyaml' :
        ensure  => present;
    }
  }

  file {
    '/usr/local/etc/gitbox-syncer':
      ensure => directory,
      mode   => '0755',
      owner  => $username,
      group  => $group;
    '/var/run/gitbox-syncer':
      ensure => directory,
      mode   => '0755',
      owner  => 'www-data',
      group  => 'www-data';
    '/x1/gitbox/sync-log.txt':
      ensure => file,
      mode   => '0755',
      owner  => 'www-data',
      group  => 'www-data';
    '/usr/local/etc/gitbox-syncer/gitbox-poller.py':
      mode   => '0755',
      owner  => $username,
      group  => $group,
      source => 'puppet:///modules/gitbox_syncer/gitbox-poller.py';
    '/usr/local/etc/gitbox-syncer/gitbox-poller.yaml':
      mode   => '0755',
      owner  => $username,
      group  => $group,
      source => 'puppet:///modules/gitbox_syncer/gitbox-poller.yaml';
    }
    # Set up systemd on first init
    -> file {
      '/lib/systemd/system/gitbox-poller.service':
        mode   => '0644',
        owner  => 'root',
        group  => 'root',
        source => "puppet:///modules/gitbox_syncer/gitbox-poller.${::operatingsystem}";
    }
    -> exec { 'staged-systemd-reload':
      command     => 'systemctl daemon-reload',
      path        => [ '/usr/bin', '/bin', '/usr/sbin' ],
      refreshonly => true,
    }
    -> service { $service_name:
        ensure    => $service_ensure,
        subscribe => [
          File['/usr/local/etc/gitbox-syncer/gitbox-poller.py']
        ]
    }
}
