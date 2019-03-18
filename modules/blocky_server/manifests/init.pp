#/etc/puppet/modules/blocky_server/manifests/init.pp

class blocky_server (
){
  
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

