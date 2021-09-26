.. start docs include

Using an analytics service with a Django project means adding Javascript
tracking code to the project templates.  Of course, every service has
its own specific installation instructions.  Furthermore, you need to
include your unique identifiers, which then end up in the templates.
Not very nice.

This application hides the details of the different analytics services
behind a generic interface, and keeps personal information and
configuration out of the templates.  Its goal is to make the basic
set-up very simple, while allowing advanced users to customize tracking.
Each service is set up as recommended by the services themselves, using
an asynchronous version of the Javascript code if possible.

.. end docs include