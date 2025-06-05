document.addEventListener('DOMContentLoaded', function () {
    // --- Work Experience ---
    const experienceWrapper = document.getElementById('experienceEntriesWrapper');
    const addExperienceBtn = document.getElementById('addExperienceBtn');
    let experienceCounter = experienceWrapper ? experienceWrapper.querySelectorAll('.experience-entry').length : 0;

    if (addExperienceBtn) {
        addExperienceBtn.addEventListener('click', function () {
            experienceCounter++;
            const newExperienceEntry = `
                <div class="experience-entry dynamic-entry resume-form-subsection" id="experienceEntry-${experienceCounter}">
                    <div class="subsection-header">
                        <h4>Work Experience #${experienceCounter + 1}</h4>
                        <button type="button" class="remove-entry-btn" data-remove="experienceEntry-${experienceCounter}">Remove</button>
                    </div>
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label" for="exp${experienceCounter}_job_title">Job Title</label>
                            <input type="text" id="exp${experienceCounter}_job_title" name="experience-${experienceCounter}-job_title" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="exp${experienceCounter}_company">Company Name</label>
                            <input type="text" id="exp${experienceCounter}_company" name="experience-${experienceCounter}-company" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="exp${experienceCounter}_location">Location</label>
                            <input type="text" id="exp${experienceCounter}_location" name="experience-${experienceCounter}-location" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="exp${experienceCounter}_start_date">Start Date</label>
                            <input type="text" id="exp${experienceCounter}_start_date" name="experience-${experienceCounter}-start_date" class="form-input" placeholder="YYYY-MM">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="exp${experienceCounter}_end_date">End Date</label>
                            <input type="text" id="exp${experienceCounter}_end_date" name="experience-${experienceCounter}-end_date" class="form-input" placeholder="YYYY-MM or Present">
                        </div>
                    </div>
                    <div class="form-group full-width" style="margin-top: 15px;">
                        <label class="form-label" for="exp${experienceCounter}_responsibilities">Responsibilities & Achievements</label>
                        <textarea id="exp${experienceCounter}_responsibilities" name="experience-${experienceCounter}-responsibilities" class="form-textarea" placeholder="Describe your roles..."></textarea>
                    </div>
                </div>`;
            if (experienceWrapper) {
                experienceWrapper.insertAdjacentHTML('beforeend', newExperienceEntry);
            }
        });
    }

    // --- Education ---
    const educationWrapper = document.getElementById('educationEntriesWrapper');
    const addEducationBtn = document.getElementById('addEducationBtn');
    let educationCounter = educationWrapper ? educationWrapper.querySelectorAll('.education-entry').length : 0;

    if (addEducationBtn) {
        addEducationBtn.addEventListener('click', function () {
            educationCounter++;
            const newEducationEntry = `
                <div class="education-entry dynamic-entry resume-form-subsection" id="educationEntry-${educationCounter}">
                    <div class="subsection-header">
                        <h4>Education #${educationCounter + 1}</h4>
                        <button type="button" class="remove-entry-btn" data-remove="educationEntry-${educationCounter}">Remove</button>
                    </div>
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label" for="edu${educationCounter}_degree">Degree / Program</label>
                            <input type="text" id="edu${educationCounter}_degree" name="education-${educationCounter}-degree" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="edu${educationCounter}_institution">Institution Name</label>
                            <input type="text" id="edu${educationCounter}_institution" name="education-${educationCounter}-institution" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="edu${educationCounter}_location">Location</label>
                            <input type="text" id="edu${educationCounter}_location" name="education-${educationCounter}-location" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="edu${educationCounter}_graduation_date">Graduation Date</label>
                            <input type="text" id="edu${educationCounter}_graduation_date" name="education-${educationCounter}-graduation_date" class="form-input" placeholder="YYYY-MM">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="edu${educationCounter}_gpa">GPA / Score (Optional)</label>
                            <input type="text" id="edu${educationCounter}_gpa" name="education-${educationCounter}-gpa" class="form-input">
                        </div>
                    </div>
                </div>`;
            if (educationWrapper) {
                educationWrapper.insertAdjacentHTML('beforeend', newEducationEntry);
            }
        });
    }

    // --- Projects ---
    const projectWrapper = document.getElementById('projectEntriesWrapper');
    const addProjectBtn = document.getElementById('addProjectBtn');
    let projectCounter = projectWrapper ? projectWrapper.querySelectorAll('.project-entry').length : 0;

    if (addProjectBtn) {
        addProjectBtn.addEventListener('click', function () {
            projectCounter++;
            const newProjectEntry = `
                <div class="project-entry dynamic-entry resume-form-subsection" id="projectEntry-${projectCounter}">
                    <div class="subsection-header">
                        <h4>Project #${projectCounter + 1}</h4>
                        <button type="button" class="remove-entry-btn" data-remove="projectEntry-${projectCounter}">Remove</button>
                    </div>
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label" for="proj${projectCounter}_name">Project Name</label>
                            <input type="text" id="proj${projectCounter}_name" name="project-${projectCounter}-name" class="form-input">
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="proj${projectCounter}_link">Project Link (Optional)</label>
                            <input type="url" id="proj${projectCounter}_link" name="project-${projectCounter}-link" class="form-input" placeholder="https://github.com/yourproject">
                        </div>
                    </div>
                    <div class="form-group full-width" style="margin-top: 15px;">
                        <label class="form-label" for="proj${projectCounter}_description">Description & Technologies</label>
                        <textarea id="proj${projectCounter}_description" name="project-${projectCounter}-description" class="form-textarea" placeholder="Describe the project..."></textarea>
                    </div>
                </div>`;
            if (projectWrapper) {
                projectWrapper.insertAdjacentHTML('beforeend', newProjectEntry);
            }
        });
    }


    // --- General Remove Button Functionality ---
    // Use event delegation for dynamically added remove buttons
    document.body.addEventListener('click', function(event) {
        if (event.target && event.target.classList.contains('remove-entry-btn')) {
            const entryIdToRemove = event.target.dataset.remove;
            const entryElement = document.getElementById(entryIdToRemove);
            if (entryElement) {
                entryElement.remove();
                // Optional: You might want to re-index counters or names if needed,
                // but for simple backend processing, unique names are often sufficient.
            }
        }
    });

    // --- Form Submission Logic (Data Collection) ---
    const resumeBuilderForm = document.getElementById('resumeBuilderForm');
    if (resumeBuilderForm) {
        resumeBuilderForm.addEventListener('submit', function (event) {
            event.preventDefault(); // Prevent default form submission

            const formData = new FormData(resumeBuilderForm);
            const resumeObject = {
                resume_name: formData.get('resume_name'),
                sections: {
                    personal_info: {
                        full_name: formData.get('pi_full_name'),
                        email: formData.get('pi_email'),
                        phone: formData.get('pi_phone'),
                        location: formData.get('pi_location'),
                        linkedin: formData.get('pi_linkedin'),
                        github: formData.get('pi_github')
                    },
                    summary: formData.get('summary_text'),
                    experience: [],
                    education: [],
                    skills: formData.get('skills_text') ? formData.get('skills_text').split(/[\n,]+/).map(skill => skill.trim()).filter(skill => skill) : [], // Split skills by newline or comma
                    projects: []
                    // Add other sections like certifications, awards here
                }
            };

            // Collect Experience Entries
            document.querySelectorAll('.experience-entry').forEach((entry, index) => {
                // Use the actual index for name attributes if they are not 0-indexed from the start
                // Or rely on the name attributes already set (experience-0-job_title, experience-1-job_title etc.)
                // For simplicity, this example assumes the backend will handle prefixed names.
                // This part needs to align with how your backend expects the data.
                // The current JS creates names like 'experience-0-job_title', 'experience-1-job_title'.
                // We need to parse these or send them as is.
                // For now, let's assume we'll construct a proper list.

                const expData = {};
                // Iterate through all input/textarea elements within this entry
                entry.querySelectorAll('input, textarea').forEach(input => {
                    // Extract the base field name (e.g., 'job_title' from 'experience-0-job_title')
                    const nameParts = input.name.split('-');
                    if (nameParts.length >= 3) {
                        const fieldName = nameParts.slice(2).join('_'); // e.g. job_title
                        if (fieldName === 'responsibilities') {
                            expData[fieldName] = input.value.split('\n').map(line => line.trim()).filter(line => line);
                        } else {
                            expData[fieldName] = input.value;
                        }
                    }
                });
                if (Object.keys(expData).length > 0 && expData.job_title) { // Add only if there's data and a title
                    resumeObject.sections.experience.push(expData);
                }
            });

            // Collect Education Entries
            document.querySelectorAll('.education-entry').forEach((entry, index) => {
                const eduData = {};
                entry.querySelectorAll('input, textarea').forEach(input => {
                    const nameParts = input.name.split('-');
                    if (nameParts.length >= 3) {
                        const fieldName = nameParts.slice(2).join('_');
                        eduData[fieldName] = input.value;
                    }
                });
                 if (Object.keys(eduData).length > 0 && eduData.degree) {
                    resumeObject.sections.education.push(eduData);
                }
            });

            // Collect Project Entries
            document.querySelectorAll('.project-entry').forEach((entry, index) => {
                const projData = {};
                entry.querySelectorAll('input, textarea').forEach(input => {
                    const nameParts = input.name.split('-');
                    if (nameParts.length >= 3) {
                        const fieldName = nameParts.slice(2).join('_');
                         if (fieldName === 'description') { // Assuming description might include technologies
                            projData[fieldName] = input.value; // Or parse further if needed
                        } else {
                            projData[fieldName] = input.value;
                        }
                    }
                });
                 if (Object.keys(projData).length > 0 && projData.name) {
                    resumeObject.sections.projects.push(projData);
                }
            });

            console.log('Submitting Resume Data:', JSON.stringify(resumeObject, null, 2));

            // Get the form action URL
            const formAction = resumeBuilderForm.getAttribute('action');

            // Submit the data as JSON
            fetch(formAction, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // If you're using Flask-WTF or other CSRF protection, include the token
                    // 'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                },
                body: JSON.stringify(resumeObject)
            })
            .then(response => {
                if (response.ok) {
                    // Handle success - maybe redirect or show a success message
                    // For now, let's assume redirection will be handled by the server response if it's not a JSON API
                    if (response.redirected) {
                        window.location.href = response.url;
                    } else {
                        return response.json().then(data => {
                            console.log('Success:', data);
                            if (data.redirect_url) {
                                window.location.href = data.redirect_url;
                            } else {
                                alert('Resume saved successfully!'); // Or update UI
                            }
                        });
                    }
                } else {
                    // Handle errors - show an error message
                    response.json().then(data => {
                        console.error('Error:', data);
                        alert('Error saving resume: ' + (data.message || 'Unknown error'));
                    }).catch(() => {
                        alert('Error saving resume. Please check the console for details.');
                    });
                }
            })
            .catch((error) => {
                console.error('Fetch Error:', error);
                alert('An error occurred while submitting the form.');
            });
        });
    }
});