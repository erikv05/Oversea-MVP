import "./App.css";
import { useState } from "react";


function App() {
  const [file, setFile] = useState(null);
  const [userNames, setUserNames] = useState([]);
  const [emails, setEmails] = useState({});
  const [selectedUser, setSelectedUser] = useState(null);

  // Function to handle file input change
  const handleFileChange = (event) => {
    event.preventDefault();
    setFile(event.target.files[0]);
  };

  // Function to parse CSV file and extract names
  const handleFileUpload = (event) => {
    event.preventDefault();
    if (!file) {
      alert("Please select a file first.");
      return;
    }

    const reader = new FileReader();
    reader.onload = function (event) {
      const text = event.target.result;
      const rows = text.split("\n");
      const names = rows.map((row) => {
        const columns = row.split(",");
        // Assuming the name is in the third column
        return columns[3].trim();
      });
      setUserNames(names);
    };
    reader.readAsText(file);
  };


const readUploadedFileAsText = (inputFile) => {
  const temporaryFileReader = new FileReader();

  return new Promise((resolve, reject) => {
    temporaryFileReader.onerror = () => {
      temporaryFileReader.abort();
      reject(new DOMException("Problem parsing input file."));
    };

    temporaryFileReader.onload = () => {
      resolve(temporaryFileReader.result);
    };
    temporaryFileReader.readAsText(inputFile);
  });
};

  // Mock function to simulate an API call for generating emails
  const generateEmails = async () => {
    try {
      const textDat = await readUploadedFileAsText(file);
      const response = await fetch("http://localhost:8080/send-email", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({data: textDat}),
        // Example: Sending user names in request's body, adjust as per your backend needs
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setEmails(data); // Assuming the API returns an object with names as keys and emails as values
      alert("Emails generated!");
    } catch (error) {
      console.error(`Could not generate emails: ${error}`);
      alert("Failed to generate emails.");
    }
  };

  // Function to handle clicks on user names
  const handleNameClick = (name) => {
    setSelectedUser(name);
  };

  return (
    <div>
      <input type="file" accept="csv" onChange={handleFileChange} />
      <button onClick={handleFileUpload}>Upload CSV</button>
      <button onClick={generateEmails} disabled={!userNames.length}>
        Generate Email
      </button>
      <div>
        {userNames.map((name, index) => (
          <div
            key={index}
            onClick={() => handleNameClick(name)}
            style={{ cursor: "pointer" }}
          >
            {name}
          </div>
        ))}
      </div>
      {selectedUser && (
        <div>
          <p>{`Email for ${selectedUser}: ${emails[selectedUser]}`}</p>
        </div>
      )}
    </div>
  );
}

export default App;
