===============================================================================
TRAVELTOGETHER - WEB APPLICATION PROJECT
Team 5

AUTHORS:
L Øyvind Nordbø: 100576766   
L Simon Volkmann: 100575156  
L Mathias Gjestad: 100576768 

===============================================================================
ADDITIONAL FUNCTIONALITY
===============================================================================

These additional features have been implemented beyond the basic requirements:

1. USER PROFILES WITH ALIASES
   - Users can set a display name (alias) instead of showing email addresses
   - Upon registering a new user, the person gets asked to set an alias and 
     profile bio
        - Full e-mail is still displayed in every user profile

2. AUTOCOMPLETE FOR LOCATIONS
   - Integration with OpenStreetMap Nominatim API
   - Real-time location suggestions for departure and destination fields
        - OpenStreetMap is limited. Not all street addresses are included but the 
        - purpose is the same.

3. AUTOMATIC PROPOSAL CLEANUP
   - When last participant leaves, the entire proposal is automatically deleted
        - Prevents orphaned proposals with no participants

===============================================================================
TEST USERS
===============================================================================

For more efficient testing, you can use the following user accounts:

User 1 (Creater of proposal):
  Email: test1@t1.com
  Password: password

User 2 (Participant w/o permissions):
  Email: test2@t2.com
  Password: password

User 3 (Newley created user, no proposals):
  Email: test3@t3.com
  Password: password

===============================================================================
IMPORTANT INFORMATION FOR TESTING
===============================================================================

DATABASE CONFIGURATION
----------------------
The application is configured to use the UC3M lab MariaDB infrastructure:
- Database: 26_webapp_34a
- Host: mysql.lab.it.uc3m.es
- User: 26_webapp_34

RUNNING THE APPLICATION
-----------------------
1. Ensure virtual environment is activated:
   source venv/bin/activate 

2. Run database migrations if needed:
   python migrate_add_proposal_fields.py

3. Start the application:
   python app.py

4. Access at: http://localhost:5000

TESTING WORKFLOW
----------------
1. Register a new user account or use test accounts above
2. Create a trip proposal with various details
3. Mark some information as "final" using checkboxes
4. Join proposals as different users to test collaboration
5. Test meetup creation with date/time
6. Try changing proposal status (close, finalize, cancel)
7. Test leaving proposals and automatic cleanup

KNOWN CONSIDERATIONS
--------------------
- Location autocomplete requires internet connection (uses OpenStreetMap API)
- Only proposal creators and users with can_edit permission can modify 
  proposals
- Proposals are automatically deleted when the last participant leaves

===============================================================================
ARTIFICIAL INTELLIGENCE DECLARATION
===============================================================================

We declare that artificial intelligence tools (specifically GitHub Copilot) were 
used during the development of this project for the following purposes:

1. CODE GENERATION AND ASSISTANCE
   - Generating boilerplate code for Flask routes and database models
   - Implementing form validation and error handling logic
   - Creating HTML templates with proper Jinja2 syntax
   - Writing SQL migration scripts

2. DEBUGGING AND OPTIMIZATION
   - Identifying and fixing bugs 
   - Optimizing database queries
   - Refactoring redundant code for better maintainability

3. DOCUMENTATION
   - Generating code comments and docstrings
   - Helping structure the README

All AI-generated code was reviewed, tested, and adapted by the team members 
to ensure it meets the project requirements and our quality standards. We 
take full responsibility for the final implementation and any issues that 
may arise from it.

The core architecture, design decisions, and business logic were conceived 
and implemented by the team members with AI serving as a development 
assistant tool.

===============================================================================
END OF README
===============================================================================
