# Linking a Launchpad account to github account for CLA accountability

In order to track which github users are authorized as having signed the Contributor License Agreement, cloud-init will track mappings of Launchpad username to GitHub usernames.

In order to validate that a GitHub user has signed the CLA, cloud-init upstream
uses the following mechanism to assert that a specific Launchpad user has accessto a GitHub account.

* Developer: sign the Canonical Contributor License Agreement](https://ubuntu.com/legal/contributors) if not already signed mentioning Josh Powers as 'Project contact' or 'Canonical Project Manager'
* Developer: propose an identical branch to Launchpad as your launchpad user and to github.com/canonical/cloud-init as your github user
  * That branch will add an entry "YOURLAUNCHPADUSER": "YOURGITHUBUSER" into the
    file tools/.lp-to-github
* Cloud-init upstream maintainers: review Launchpad and GitHub branches
* Cloud-init upstream maintainers: Merge the Launchpad branch into github
* Cloud-init upstream maintainers: Merge the Launchpad branch into github


## Developer procedure
### Propose an equivalent branch in Launchpad and GitHub. Adding LP->github user mapping.
Below `LP_USER` should be your launchpad username, `GH_USER` should be your github username.
* Login to github and Fork the cloud-init project from https://github.com/canonical/cloud-init
* Clone the upstream repo from https://github.com/cannonical/cloud-init and run a tool to automatically create mirrored branches in Launchpad and GitHub
```
git clone git@github.com:canonical/cloud-init.git
cd cloud-init

# This script automatically creates a launchpad branch and github branch to add your user mapping
./tools/migrate-lp-user-to-github LP_USER GH_USER

* Make sure to have manually created the pull request in Github as prompted by migrate script


## Upstream procedure
* Review both github and launchpad branches for the user
* Ensure launchpad user has signed the CLA: https://launchpad.net/~contributor-agreement-canonical
* Approve the Launchpad branch
* Run `review-mps` script as your `LP_USER` and select the merge proposal you just approved
```
review-mps --git-user LP_USER  --merge --skip tests --push-remote git@github.com:canonical/cloud-init -v
```
* Manually close and comment on the github PR for this user
  "Validated launchpad to github user mapping"
