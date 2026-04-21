# Fitt-with-Pitt
CS1530 Group 8 Health and Fitness Project

## Testing

The project now includes a pytest-based behavioral test suite in `tests/`.

### What the suite covers

- authentication and access control
- user registration and login behavior
- nutrition logging and daily summary calculations
- workout logging and weekly progress behavior
- goals page updates for nutrition, activity, and weight goals
- dashboard integration so saved goals show up in tracking visuals
- authorization checks for deleting another user's data

### Run the suite

1. Install dependencies from `requirements.txt`
2. Run `pytest`

### Testing approach

The current suite is behavior-first. It focuses on the routes and user-visible flows that matter most:

- route protection for logged-out users
- form submissions that create or update tracked data
- persistence of saved goals
- cross-page integration between goals, logging pages, and the dashboard

As the project grows, the next useful additions would be:

- edge-case validation tests for invalid form inputs
- more authorization tests for activity and weight data
- visual regression or browser-based smoke tests for key pages
- unit tests for helper functions if the route logic is split into services
