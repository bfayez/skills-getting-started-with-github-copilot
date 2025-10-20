document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Helper function to show messages
  function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");

    // Hide message after 5 seconds
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;
        
        // Create participants list HTML
        let participantsHtml = '';
        if (details.participants.length > 0) {
          const participantsList = details.participants.map(email => {
            // Extract name from email (everything before @)
            const participantName = email.split('@')[0];
            // Capitalize first letter of each word and replace dots/underscores with spaces
            const displayName = participantName.replace(/[._]/g, ' ')
              .split(' ')
              .map(word => word.charAt(0).toUpperCase() + word.slice(1))
              .join(' ');
            return `
              <div class="participant-item" data-email="${email}" data-activity="${name}">
                <span class="participant-name">${displayName}</span>
                <button class="delete-participant-btn" title="Remove participant">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>
            `;
          }).join('');
          
          participantsHtml = `
            <div class="participants-section">
              <p><strong>Current Participants:</strong></p>
              <div class="participants-list">
                ${participantsList}
              </div>
            </div>
          `;
        } else {
          participantsHtml = `
            <div class="participants-section">
              <p><strong>Current Participants:</strong></p>
              <p class="no-participants">No participants yet - be the first to join!</p>
            </div>
          `;
        }

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          ${participantsHtml}
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners for delete buttons
      document.querySelectorAll('.delete-participant-btn').forEach(button => {
        button.addEventListener('click', async (event) => {
          event.preventDefault();
          
          const participantItem = event.target.closest('.participant-item');
          const email = participantItem.dataset.email;
          const activityName = participantItem.dataset.activity;
          
          if (confirm(`Are you sure you want to remove this participant from ${activityName}?`)) {
            try {
              const response = await fetch(
                `/activities/${encodeURIComponent(activityName)}/unregister?email=${encodeURIComponent(email)}`,
                {
                  method: "DELETE",
                }
              );

              const result = await response.json();

              if (response.ok) {
                // Show success message
                showMessage(result.message, 'success');
                
                // Refresh activities list to show updated participants
                fetchActivities();
              } else {
                showMessage(result.detail || "Failed to remove participant", 'error');
              }
            } catch (error) {
              showMessage("Failed to remove participant. Please try again.", 'error');
              console.error("Error removing participant:", error);
            }
          }
        });
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, 'success');
        signupForm.reset();
        
        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", 'error');
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", 'error');
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
