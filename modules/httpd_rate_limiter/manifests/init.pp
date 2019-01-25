#/etc/puppet/modules/httpd_rate_limiter/manifests/init.pp

# requires lua dependencies in basepackages on target host

# base::basepackages:
# - 'lua5.2'
# - 'mod-lua-asf'

class httpd_rate_limiter (
  $interval                 = '120',
  $cpumax                   = '90',
  $autoconf                 = false,
){


  file {
    '/var/www/rate-limit.lua':
      ensure  => present,
      owner   => 'root',
      group   => 'root',
      mode    => '0755',
      content => template('httpd_rate_limiter/rate-limit.lua.erb');
  }
  
  if $autoconf {
      apache::mod { 'lua': }
      apache::custom_config {
        'rate-limit':
          ensure   => present,
          filename => 'rate-limit.conf',
          content  => template('httpd_rate_limiter/rate-limit.conf.erb'),
      }
  }

}
