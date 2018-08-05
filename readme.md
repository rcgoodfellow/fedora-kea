# Kea RPM build instructions

```shell
# get sources into build tree
spectool -g -R kea.spec

# place spec and patches in build tree
cp kea.spec ~/rpmbuild/SPECS/
cp *.patch ~/rpmbuild/SOURCES/

# build
cd ~/rpmbuild/SPECS rpmbuild -ba kea.spec
```
