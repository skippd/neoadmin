# neoadmin

This project aims to provide a Administration UI for neo4j




### UI screenshots
Homepage
![Homepage](/readmeimages/dashboard.PNG)

Node creation page
![Node Creation](/images/Createnode.PNG)

### Functions Available

* Search Nodes
* Create Nodes
* Edit Nodes
* Delete Nodes
* Add relations
* Delete Relations
* Scrub through all nodes in a label

## Usage

### Running Django Example app

  Clone the git repository and navigate to the root folder of the repository

  ```
  git clone https://github.com/skippd/neoadmin.git
  cd neoadmin/django-example-app
  ```

  Install the requirement

  ```
  pip install -r requirements.txt
  ```

  Open settings present in django-example-app > myprojects > settings.py and update the connection details to connect to neo4j
  Update the following line with the format showed
  ```
  config.DATABASE_URL = 'bolt://<username>:<password>@<host>:<port>'
  ```

  start the Application
  ```
  python manage.py runserver
  ```

  Go to http://localhost:8000/admin and login with ```Username = admin , Password = admin```
  Now the dashboard is available at https://localhost:8000/neoadmin

### Integrating with existing django Application

  Note : This is built on python 3.6 and django 2.2.4
  Copy the neoadmin folder in root to your django application

#### Install the requirements

  ```
  pip install neomodel==3.3.1
  pip install pandas==1.0.1
  ```

#### Url config

  add a entrypoint for neoadmin in your url.py

  ```
  from neoadmin import urls as neourls
    ...
  urlpatterns = [
                ...
                path('neoadmin/', include(neourls)),
                ]
  ```

#### Setting config

  Open your setting file and do the following configs

   - Add the app into django apps
  ```
  INSTALLED_APPS = [
      ...
      'neoadmin',
  ]
  ```

  - Add the connection details in setting file
  ```
  from neomodel import config
  config.DATABASE_URL = 'bolt://neo4j:123456789@localhost:7687'
  ```
  - Add the home url for neoadmin (entry point which is added in urls file)
  in the above case it is
  ```
  NEOADMIN_HOME = '/neoadmin/'
  ```

  That's it, now got to the entry point after starting the apllication and you can see the dashboard
