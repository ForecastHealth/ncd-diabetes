// runList.js

class RunList {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.runs = [];
    }

    addRun(taskId, modelName, countryName) {
        const run = {
            taskId,
            modelName,
            countryName,
            status: 'Pending',
            timestamp: new Date().toLocaleString(),
            downloadUrl: null
        };
        this.runs.unshift(run);
        this.render();
        return run;
    }

    updateRunStatus(taskId, status, downloadUrl = null) {
        const run = this.runs.find(r => r.taskId === taskId);
        if (run) {
            run.status = status;
            run.downloadUrl = downloadUrl;
            this.render();
        }
    }

    render() {
        this.container.innerHTML = '';
        const table = document.createElement('table');
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Model</th>
                    <th>Country</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;

        const tbody = table.querySelector('tbody');
        this.runs.forEach(run => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${run.timestamp}</td>
                <td>${run.modelName}</td>
                <td>${run.countryName}</td>
                <td>${run.status}</td>
                <td>${this.getActionButton(run)}</td>
            `;
            tbody.appendChild(tr);
        });

        this.container.appendChild(table);
    }

    getActionButton(run) {
        if (run.status === 'Success' && run.downloadUrl) {
            return `<a href="${run.downloadUrl}" download class="download-btn">Download</a>`;
        } else if (run.status === 'Pending' || run.status === 'In Progress') {
            return `<button onclick="runList.checkStatus('${run.taskId}')" class="status-btn">Check Status</button>`;
        } else {
            return '';
        }
    }

    checkStatus(taskId) {
        const statusUrl = `https://api.forecasthealth.org/pipeline/status/${taskId}`;
        fetch(statusUrl)
            .then(response => response.json())
            .then(data => {
                console.log('Received status:', data.status);
                if (data.status === "SUCCESS" && data.result && data.result.download_url) {
                    this.updateRunStatus(taskId, 'Success', data.result.download_url);
                } else if (data.status === "PENDING" || data.status === "PROGRESS") {
                    this.updateRunStatus(taskId, 'In Progress');
                } else {
                    this.updateRunStatus(taskId, 'Error');
                }
            })
            .catch(error => {
                console.error('Error checking status:', error);
                this.updateRunStatus(taskId, 'Error');
            });
    }
}

// Global instance
const runList = new RunList('runList');