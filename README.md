# Welcome
This script automates the distribution of billing information to my other roomates. It gets the information to calculate the total bill from multiple emails:
- Hydro email
- Winnipeg waste and water email
- Email received from roomates about how much they spent on groceries for the entire household
- Some hardcoded values (I know, this needs further improvement)

Once it calculates the total bill, it sends an email to me and my roomates depending on how much we owe to the household. I manage the bills so most of the time they send the money to me.

# TODO
- Migrate from IMAP to Oauth for authentication and retrieval of email messages
- Refactor code
