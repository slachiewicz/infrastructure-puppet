#/etc/puppet/modules/httpd_blocky/manifests/init.pp

# requires mod_lua capable host (ubu >= 16.04)
# and httpd on the box, or it will ignore things.

class httpd_blocky (
  $required_packages = ['lua-cjson', 'lua-sec', 'lua-bitop'],
  ){

  package {
    $required_packages:
      ensure => 'present',
  }
  
  # Make sure we are using httpd here
  if defined(Class['apache']) {
    file {
      '/var/www/blocky_check.lua':
        ensure => present,
        owner  => 'root',
        group  => 'root',
        mode   => '0755',
        source => 'puppet:///modules/httpd_blocky/blocky_check.lua';
      '/var/www/ip.lua':
        ensure => present,
        owner  => 'root',
        group  => 'root',
        mode   => '0755',
        source => 'puppet:///modules/httpd_blocky/ip.lua';
    }
    apache::custom_config {
      'rate-limit':
        ensure   => present,
        filename => 'httpd-blocky.conf',
        source   => 'puppet:///modules/httpd_blocky/httpd-blocky.conf';
    }
  }
}
