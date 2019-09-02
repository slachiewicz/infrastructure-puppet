#/etc/puppet/modules/staged/manifests/init.pp

class staged (
  $service_name   = 'staged',
  $shell          = '/bin/bash',
  $service_ensure = 'running',
  $username       = 'www-data',
  $group          = 'www-data'
) {
    package { 'python3-pip': ensure => installed }
    exec { "pip3_asfpy":
      command => "pip3 install asfpy",
      unless => "pip3 list | grep asfpy",
      path => '/bin:/usr/bin',
      require => Package['python3-pip']
    }
    exec { "pip3_pyyaml":
      command => "pip3 install pyyaml",
      unless => "pip3 list | grep pyyaml",
      path => '/bin:/usr/bin',
      require => Package['python3-pip']
    }
    # dir and py script
    file {
      '/usr/local/etc/staged':
        ensure => directory,
        mode   => '0755',
        owner  => $username,
        group  => $group;
      '/var/run/staged':
        ensure => directory,
        mode   => '0755',
        owner  => $username,
        group  => $group;
      '/usr/local/etc/staged/staged.py':
        mode    => '0755',
        owner   => $username,
        group   => $group,
        source => "puppet:///modules/staged/staged.py";
    }
    # Set up systemd on first init
    -> file {
      '/lib/systemd/system/staged.service':
        mode   => '0644',
        owner  => 'root',
        group  => 'root',
        source => "puppet:///modules/staged/staged.service";
    }
    -> exec { 'staged-systemd-reload':
      command     => 'systemctl daemon-reload',
      path        => [ '/usr/bin', '/bin', '/usr/sbin' ],
      refreshonly => true,
    }
    # Ensure, after systemd set up, that staged is running
    -> service { $service_name:
        ensure    => $service_ensure,
        subscribe => [
          File['/usr/local/etc/staged/staged.py']
        ]
    }
}
