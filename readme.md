This is complete frontend and backed developed but there is another algorithm attached which uses data structures and algorithms so please look into it.

# **3D Rubik's Cube Solver**

## **1\. Overview**

This is a full-stack web application that allows users to input the state of a 3x3 Rubik's Cube through an interactive 3D interface and receive the step-by-step solution to solve it. The project combines a visually engaging frontend with a powerful backend solving engine.

## **2\. Features**

* **Interactive 3D Cube:** A fully interactive 3D cube rendered with HTML and CSS that can be rotated by clicking and dragging.  
* **Intuitive Color Input:** Users can easily set the colors of each sticker on the cube by clicking on them.  
* **Layer-by-Layer (LBL) Solver:** The backend uses a robust LBL algorithm to find an efficient solution to any valid cube state.  
* **Real-time Validation:** The application checks if the entered cube state is valid (i.e., has exactly 9 stickers of each color) before attempting to solve.  
* **Sleek, Modern UI:** A dark-themed, responsive user interface designed for a great user experience.

## **3\. Tech Stack**

* **Frontend (Client-Side):**  
  * **HTML5:** For the basic structure of the web page.  
  * **CSS3:** For styling, animations, and creating the 3D cube effect.  
  * **JavaScript (ES6+):** For DOM manipulation, user interaction, 3D cube rotation physics, and communication with the backend.  
* **Backend (Server-Side):**  
  * **Python:** The core language for the solving logic.  
  * **Flask:** A lightweight web framework used to create the API that the frontend communicates with.

## **4\. How It Works**

The application's workflow is a classic example of a client-server architecture. Here is a step-by-step breakdown of the process from user input to final output.

### **Step 1: User Input (Setting the Cube Colors)**

* The user interacts with the 3D cube on the webpage.  
* They can click and drag the mouse to rotate the cube and view all its faces.  
* To change the color of a sticker, the user simply clicks on it. The cube-interactive.js script cycles through a predefined list of colors (\['W', 'R', 'G', 'Y', 'O', 'B'\]) and updates the sticker's appearance.

### **Step 2: Processing the Input (Frontend)**

* When the user clicks the **"Solve Cube"** button, the JavaScript code springs into action.  
* It iterates through all 54 stickers on the cube and reads their current color value, which is stored in a data-value attribute.  
* It assembles this information into a JSON object that represents the entire cube's state. The structure looks like this:

{  
  "U": \[\["W", "W", "W"\], \["W", "W", "W"\], \["W", "W", "W"\]\],  
  "L": \[\["O", "O", "O"\], \["O", "O", "O"\], \["O", "O", "O"\]\],  
  "F": \[\["G", "G", "G"\], \["G", "G", "G"\], \["G", "G", "G"\]\],  
  "..."  
}

* Before sending, it performs a quick validation to ensure there are exactly 9 stickers of each of the 6 colors. If not, it displays an error message.

### **Step 3: Sending the Data to the Server**

* The JavaScript uses the fetch API to send an HTTP POST request to the /solve endpoint on the backend server.  
* The JSON object containing the cube's state is included in the body of this request.

### **Step 4: The Backend Solver Engine (Python & Flask)**

* The Flask application (app.py) is listening for requests. The @app.route('/solve', methods=\['POST'\]) decorator tells it to execute a specific function when a POST request arrives at this URL.  
* Flask automatically parses the incoming JSON data.  
* The data is passed to an instance of the CubeSolver class.  
* The CubeSolver class implements a **Layer-by-Layer (LBL)** algorithm. It executes a series of methods in a specific order to solve the cube:  
  1. \_solve\_white\_cross()  
  2. \_solve\_white\_corners()  
  3. \_solve\_second\_layer()  
  4. \_solve\_yellow\_cross()  
  5. \_solve\_yellow\_face()  
  6. \_solve\_final\_layer()  
* As the solver executes its algorithms, it logs each move (e.g., "R", "U'", "F2") in a list.

### **Step 5: Sending the Output Back to the Frontend**

* Once the solver has finished, the backend has a complete list of moves that form the solution.  
* Flask packages this list into a JSON response, which looks something like this:

{  
  "solution": \["R", "U", "R'", "U'", "..."\],  
  "sequence": "R U R' U'..."  
}

* This JSON is sent back to the browser as the response to the initial fetch request.

### **Step 6: Displaying the Solution**

* The JavaScript code in the browser receives the response from the server.  
* It checks if the response is valid and then parses the JSON to access the solution.  
* Finally, it takes the sequence string from the JSON and displays it in the output box on the webpage, allowing the user to see the solution.

## **5\. How to Run This Project Locally**

### **Prerequisites**

* Python 3.x  
* pip (Python package installer)

### **Installation**

1. **Clone the repository or download the files.**  
2. **Navigate to the project directory:**  
   cd path/to/your/project

3. **Install the required Python package (Flask):**  
   pip install Flask

4. **Run the Flask application:**  
   python app.py

5. **Open your web browser** and go to the following address:  
   http://127.0.0.1:5000

You should now see the 3D Rubik's Cube Solver running in your browser.