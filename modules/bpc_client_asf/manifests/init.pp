# bpc_client_asf

# this class exists only to prevent build and tlp nodes from being backed 
# up unlike every other ubuntu host. it could easily be extended later if
# there are other one-off machines which shouldn't be backed up

class bpc_client_asf {

    if ($::noderole !~ /jenkins/) and
       ($::noderole !~ /tlpserver/) and
       ($::noderole !~ /buildbot/) 
    {
      include backuppc::client
    }
}
