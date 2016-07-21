# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "debian/jessie64"

  config.vm.hostname = "mail.medicustek.test"
  config.vm.network "private_network", ip: "172.16.0.5"
  config.vm.network "forwarded_port", guest: 25, host: 2525

  config.vm.synced_folder "test_notifications/", "/var/mail"
  
  config.vm.provider "virtualbox" do |vb|
    vb.gui = false 
    vb.memory = "512"
    vb.cpus = "1"
    vb.name = "notification-service-email"
  end

  config.vm.provision "ansible_local" do |ansible|
    ansible.playbook = "resources/fakesmtp.yml"
  end
end
