# Orthanc quickstart using docker on linux

We use the containers [suggested in the Orthanc documentation](https://book.orthanc-server.com/users/docker.html#usage-with-plugins-enabled).

Create some directories in which to save the Orthanc config file and the persistent database:

```sh
mkdir ~/.orthanc-docker/
mkdir ~/.orthanc-docker/db/
```

Pull the container for Orthanc with plugins (plugins needed for DICOMWeb), and save the default config file:

```sh
docker run --rm --entrypoint=cat jodogne/orthanc-plugins:1.12.1 /etc/orthanc/orthanc.json > ~/.orthanc-docker/config.json
```

Now edit `~/.orthanc-docker/config.json` to turn off authentication by keeping `RemoteAccessAllowed` as `true` but explicitly setting `AuthenticationEnabled` as `false`.

This completes the first-time setup.

To start the server:

```sh
docker run -p 4242:4242 -p 8042:8042 --rm -v ~/.orthanc-docker/config.json:/etc/orthanc/orthanc.json:ro -v ~/.orthanc-docker/db/:/var/lib/orthanc/db/ jodogne/orthanc-plugins:1.12.1
```