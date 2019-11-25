#/etc/puppet/modules/genmeta_ldap/manifests.init.pp

class genmeta_ldap(
  # Located in eyaml
  $genmeta_rw_pw = '',
) {

  file {
    '/usr/local/bin/refresh_meta.sh':
      ensure => present,
      mode   => '0770',
      owner  => root,
      group  => root,
      source => 'puppet:///modules/genmeta_ldap/refresh_meta.sh';
    '/root/.genmeta_rw.txt':
      ensure  => present,
      mode    => '0600',
      owner   => root,
      group   => root,
      content => $genmeta_rw_pw;
  }
  cron {
    'Refresh ou=meta':
      user        => root,
      minute      => '19',
      command     => '/usr/local/bin/refresh_meta.sh',
      environment => 'PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin\nSHELL=/bin/sh';
  }
}
