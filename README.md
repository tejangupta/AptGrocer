## AptGrocer
AptGrocer is a web application that helps users create grocery lists and track their expenses.
It is built using the Flask web framework and MongoDB Atlas database.
The application allows users to manage their grocery shopping experience by creating and tracking grocery lists,
adding and removing items, and keeping track of expenses for each list.

### Technologies Used
**Frontend Languages**: HTML, CSS and Client-Side JavaScript<br>
**Frontend Framework**: Bootstrap<br>
**Frontend Library**: jQuery<br>
**Backend**: Server-Side JavaScript<br>
**Backend Framework**: Flask<br>
**Database**: MongoDB

### Project Features
1. **User Login / Logout**: User need to create an account to make any kind of purchases but to check products and other searches do not require user to be logged in. First user need to be getting registered and logged in to check for recent activities, transactions, access e-wallet and items cart. For creating an account, user need to click on signup button and fulfill all create an account form requirement to get registered. In case you want to be logged in, you need to go to sign in and provide credentials which has been set up. In case user has forgotten the password, a link for setting up the same is sent to the email you provide.
2. **User Dashboard**: To change user information and other settings, I developed modules in the dashboard panel, but user can also find all these options in the top right corner of the page when a user clicks on his/her name.
- **Account Settings**: This module provides a panel to change users' profile and password information.
- **Payment Settings**: This module helps the user to store card information for easy pay and order functionality
- **Wallet Settings**: In this module user can maintain its e-cash by adding more cash or purchasing items without using any card information. User can add cash from saved cards, or use other than save card, but user can add maximum of $1,000 at one transaction and overall $10,000 are allowed. At the same time user can check for its wallet activities and details on the same page.
- **Order History**: This feature helps the user to check all the past purchases and other details such as date of purchase, products purchased, and payment information.
- **Newsletters**: Users can manage and subscribe or unsubscribe to our neweletters.
- **Logout**: User can successfully log out to avoid exploitation of its account.
3. **User Cart**: User can add items or remove items or edit the quantity for each item (maximum 5 quantities per product is allowed). Here user can check for total payment information and proceed to checkout.
4. **Search Product**: User can search by typing product's id, name, brand, and category in the search bar that is present on the top of the page.
5. **Filtered Search**: User can refine its search according to price range and category. This feature will be available in search results.
6. **Category Search**: User can directly search for products according to its category by selecting categories on the left top corner of the page right next to the logo.
7. **Product Information**: User can check for the product information by clicking on the heading or a given view button on each product thumbnail and discover more about the product and can add it to its cart by clicking on Add to Cart button under the display picture of an item.
8. **Others**: I have implemented a fake gateway where user can select the mode of payment ie saved card, new card and wallet. User can pay for the amount by any of the listed modes and also and review its payment information at the bottom and then can pay and proceed to the final step which is confirmation. Where a confirmation message will be displayed, and a transaction order is generated (which would also be available in user dashboard).

### Installation
To run AptGrocer on your local machine, follow these steps:
1. Clone the repository: ``git clone https://github.com/tejangupta/AptGrocer.git``
2. Navigate to the project directory: ``cd AptGrocer``
3. Install the required dependencies: ``pip install -r requirements.txt``
4. Start the Flask development server: ``flask run``
5. Open the web application in a browser by visiting ``http://localhost:5000``

### Contributing
If you would like to contribute to AptGrocer, please create a pull request.
Before submitting a pull request, please ensure that your code passes all tests and follows PEP 8 coding standards.

### License
AptGrocer is licensed under the MIT License.
Feel free to use, modify and distribute the code as per the terms of the license.