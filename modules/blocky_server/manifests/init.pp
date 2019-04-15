#/etc/puppet/modules/blocky_server/manifests/init.pp

class blocky_server (
){
  # Checkout blocky code from git
  # Ensure that it is the latest version.
  vcsrepo { '/blocky/blocky2':
    ensure   => latest,
    provider => git,
    source   => 'https://github.com/apache/infrastructure-blocky',
  }

  # Install and configure Apache webserver
  # sites:
  #  - blocky
  #  - uls
  apache::custom_config { 'blocky-ssl':
      ensure   => present,
      source   => 'puppet:///modules/blocky_server/blocky-ssl.conf',
      confdir  => '/etc/apache2/sites-available',
      priority => '25',
      require  => Class['apache'],
  }
  # Apache webserver module inclusions
  include apache::mod::cache
  include apache::mod::expires
  include apache::mod::rewrite
  include apache::mod::ssl
  include apache::mod::status
  include apache::mod::wsgi
  
  # Enable the blocky website in Apache webserver
  exec {
    'enable-blocky-site':
      command => '/usr/sbin/a2ensite 25-blocky-ssl',
      unless  => '/usr/bin/test -f /etc/apache2/sites-enabled/25-blocky-ssl',
      creates => '/etc/apache2/sites-enabled/25-blocky-ssl',
  }
  # Gunicorn for blocky server
  # Run this command unless gunicorn is already running.
  # -w 10 == 10 workers, we can up that if need be.
  exec { '/usr/bin/gunicorn3 -w 8 -b 127.0.0.1:8000 -D handler:application':
    path   => '/usr/bin:/usr/sbin:/bin',
    user   => 'root',
    group  => 'root',
    cwd    =>  '/blocky/blocky2/server/api/',
    unless => '/bin/ps ax | /bin/grep -q [g]unicorn',
  }
}

