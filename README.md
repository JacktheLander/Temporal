# Temporal
I used Temporal SDK to orchestrate an order lifecycle with strong data integrity and a verbose gui for managing online orders.

It uses a MySQL database with idempotent writes to ensure that the information state is maintained. 
This is tested with activities that have a high probability of failure, which I use Temporal workers with a retry policy to complete in a sequential order flow that takes less than 15 seconds.
A parent workflow is defined with a child workflow that it calls to complete the order by handling the shipping process in a separate queue.
A Flask application is used to expose REST API endpoints to call the various functions of the program.
