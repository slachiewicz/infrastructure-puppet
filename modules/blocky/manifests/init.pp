#/etc/puppet/modules/blocky/manifests/init.pp

class blocky (
  $service_name   = 'blocky',
  $shell          = '/bin/bash',
  $service_ensure = 'running',
  $username       = 'root',
  $group          = 'root',
)
{

  require python
  
  python::pip {
    'netaddr' :
      ensure => present;
    'asfpy' :
      ensure  => present;
    'requests' :
      ensure => present;
    'pyyaml' :
      ensure  => present;
    }


  file {
    '/usr/local/etc/blocky':
      ensure => directory,
      mode   => '0755',
      owner  => $username,
      group  => $group;
    '/etc/init.d/blocky':
      mode   => '0755',
      owner  => $username,
      group  => $group,
      source => "puppet:///modules/blocky/blocky.${::asfosname}";
    '/usr/local/etc/blocky/blocky.py':
      mode   => '0755',
      owner  => $username,
      group  => $group,
      source => 'puppet:///modules/blocky/blocky.py';
    '/usr/local/etc/blocky/blocky.yaml':
      mode   => '0755',
      owner  => $username,
      group  => $group,
      source => 'puppet:///modules/blocky/blocky.yaml';
    }

    -> service { $service_name:
        ensure    => $service_ensure,
        enable    => true,
        hasstatus => true,
        subscribe => [
          File['/usr/local/etc/blocky/blocky.py'],
          File['/usr/local/etc/blocky/blocky.yaml']
        ]
    }
}
