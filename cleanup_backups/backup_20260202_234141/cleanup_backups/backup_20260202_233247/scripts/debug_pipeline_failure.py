#!/usr/bin/env python3
"""
Debug Pipeline Failure - Find out why jobs are stuck in processing
"""

import requests
import json
import time

def get_job_details():
    """Get details of failed jobs"""
    try:
        response = requests.get('http://localhost:8000/api/jobs')
        if response.status_code == 200:
            jobs = response.json()
            print(f"Found {len(jobs)} jobs")
            
            for i, job in enumerate(jobs[:3]):  # Check first 3 jobs
                print(f"\n--- Job {i+1} ---")
                print(f"ID: {job['id']}")
                print(f"Status: {job['status']}")
                print(f"Progress: {job['progress']}%")
                print(f"Current Agent: {job.get('current_agent', 'None')}")
                print(f"Created: {job.get('created_at', 'Unknown')}")
                
                if 'error' in job and job['error']:
                    print(f"ERROR: {job['error']}")
                
                # Get detailed job info
                job_response = requests.get(f'http://localhost:8000/api/jobs/{job["id"]}')
                if job_response.status_code == 200:
                    job_detail = job_response.json()
                    
                    if 'logs' in job_detail and job_detail['logs']:
                        print("Recent logs:")
                        for log in job_detail['logs'][-5:]:  # Last 5 logs
                            print(f"  {log['timestamp']}: {log['message']}")
                    
                    if 'state' in job_detail:
                        state = job_detail['state']
                        print(f"State keys: {list(state.keys()) if isinstance(state, dict) else 'Not a dict'}")
                        
                        if isinstance(state, dict):
                            if 'errors' in state and state['errors']:
                                print("State errors:")
                                for error in state['errors'][-3:]:  # Last 3 errors
                                    print(f"  {error.get('agent_type', 'Unknown')}: {error.get('message', 'No message')}")
        else:
            print(f"Failed to get jobs: {response.status_code}")
            
    except Exception as e:
        print(f"Error getting job details: {e}")

def test_simple_job():
    """Submit a simple job to test the pipeline"""
    print("\n" + "="*50)
    print("Testing Simple Job Submission")
    print("="*50)
    
    try:
        # Submit a simple job
        job_data = {
            "paper_input": {
                "type": "title",
                "content": "Simple Test Paper About Machine Learning"
            },
            "options": {
                "target_duration": 30,
                "video_quality": "low",
                "parallel_processing": False
            }
        }
        
        response = requests.post('http://localhost:8000/api/jobs', json=job_data)
        if response.status_code == 200:
            job = response.json()
            job_id = job['id']
            print(f"✅ Job submitted: {job_id}")
            
            # Monitor for 30 seconds
            for i in range(6):  # 6 checks over 30 seconds
                time.sleep(5)
                
                job_response = requests.get(f'http://localhost:8000/api/jobs/{job_id}')
                if job_response.status_code == 200:
                    job_detail = job_response.json()
                    status = job_detail['status']
                    progress = job_detail['progress']
                    agent = job_detail.get('current_agent', 'None')
                    
                    print(f"Check {i+1}: Status={status}, Progress={progress}%, Agent={agent}")
                    
                    if status in ['completed', 'failed']:
                        break
                        
                    if 'logs' in job_detail and job_detail['logs']:
                        latest_log = job_detail['logs'][-1]
                        print(f"  Latest: {latest_log['message']}")
            
            return job_id
        else:
            print(f"❌ Job submission failed: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error testing job: {e}")
        return None

def main():
    print("🔍 RASO Pipeline Failure Debug")
    print("="*50)
    
    # Check existing jobs
    print("1. Checking existing jobs...")
    get_job_details()
    
    # Test new job
    print("\n2. Testing new job...")
    job_id = test_simple_job()
    
    if job_id:
        print(f"\n3. Final check on job {job_id}...")
        time.sleep(2)
        get_job_details()

if __name__ == "__main__":
    main()