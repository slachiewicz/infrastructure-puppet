# distribute updated CA cert to puppet3 client

class update_ca {

  file { '/etc/puppet/ssl/certs/ca.pem': 
   source => 'puppet:///modules/update_ca/ca.pem', 
   owner => 'puppet', 
   group => 'puppet', 
 }

}
