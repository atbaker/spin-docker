# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"
FORWARD_DOCKER_PORTS = ENV['FORWARD_DOCKER_PORTS']

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.

  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = "phusion/precise64-docker-ready"
  config.vm.box_url = "https://oss-binaries.phusionpassenger.com/vagrant/boxes/ubuntu-12.04.3-amd64-vbox.box"

  # Use this box URL for VMware Fusion
  # config.vm.box_url = "https://oss-binaries.phusionpassenger.com/vagrant/boxes/ubuntu-12.04.3-amd64-vmwarefusion.box"

  # config.vm.network :public_network
  config.vm.network :forwarded_port, guest: 80, host: 8080
  config.vm.synced_folder ".", "/var/www/spin-docker"

  config.vm.provision "ansible" do |ansible|
      ansible.playbook = "ansible_playbook/spin_docker.yml"
      ansible.sudo = true
      ansible.host_key_checking = false
      ansible.extra_vars = { vagrant_box: true }
      # ansible.verbose = "v"
  end

  if !FORWARD_DOCKER_PORTS.nil?
    (49000..49900).each do |port|
      config.vm.network :forwarded_port, :host => port, :guest => port
    end
  end

end
