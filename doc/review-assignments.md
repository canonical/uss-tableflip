# Table Flip Review Assignment Process

## cloud-init

At stand-up each day, team will assign any new pull requests for
review.  This assignment is done algorithmically, to simplify matters:

* New pull requests are assigned from lowest number to highest (i.e.
  older first)
* The order in which pull requests assignees are selected is determined
  by the daily triage order, starting from whoever is on triage duty
  today
    * Currently that order is: Dan, Ryan, Chad
    * For example, on a Wednesday (Ryan's triage day), the first PR
      would be assigned to Ryan, the second to Chad, and the third to
      Dan
* On a day where a reviewer isn't on triage, the next triager who is a
  reviewer will be considered to be "first"
    * For example, on Fridays, whoever is on rotating Monday triage
      will be assigned the first PR.
* When a reviewer is assigned to a PR, this means they should be a
  literal Assignee on the pull request in GitHub terms


### Dealing with backlog

When the team is dealing with a backlog of reviews, the above process
will be followed for new pull requests.  If there are any team members
not assigned a new pull request, then they will be assigned _old_ pull
requests in the same fashion.
