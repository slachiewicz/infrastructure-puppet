#/etc/puppet/modules/blocky_server/manifests/init.pp

class blocky_server (
){

# Install apache
  apache::custom_config { 'blocky.apache.org':
      ensure   => present,
      source   => 'puppet:///modules/blocky_server/files/blocky-ssl.conf',
      confdir  => '/etc/apache2/sites-available',
      priority => '10',
      require  => Class['apache'],
  }

  include apache::mod::cache
  include apache::mod::expires
  include apache::mod::rewrite
  include apache::mod::ssl
  include apache::mod::status
  include apache::mod::wsgi
  
  # Checkout latest blocky code from git
  vcsrepo { '/blocky/blocky2':
    ensure   => latest,
    provider => git,
    source   => 'https://github.com/apache/infrastructure-blocky',
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

