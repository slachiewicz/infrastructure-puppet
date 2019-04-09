#/etc/puppet/modules/blocky_server/manifests/init.pp

class blocky_server (
){
  # Checkout latest blocky code from git
  vcsrepo { '/blocky/blocky2':
    ensure   => latest,
    provider => git,
    source   => 'https://github.com/apache/infrastructure-blocky',
  }
  # Copy the httpd config file for the blocky site.
  # This is a template in case it needs modification
  # not because it currently does.
  file { '/etc/apache2/sites-available/25-blocky-ssl.conf':
    ensure   => file,
    content  => template('25-blocky-ssl.conf.erb'),
    user     => 'root',
    owner    => 'root',
    mode     => 0644,
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

