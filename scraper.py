import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_shl_catalog():
    base_url = "https://www.shl.com"
    catalog_url = "https://www.shl.com/solutions/products/product-catalog/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    all_assessments = []
    
    # The catalog has pagination - we need to go through all pages
    # Individual Test Solutions filter
    params_list = [
        {"start": 0, "type": "1"},   # page 1
        {"start": 12, "type": "1"},  # page 2
        {"start": 24, "type": "1"},  # page 3
        {"start": 36, "type": "1"},  # page 4
        {"start": 48, "type": "1"},  # page 5
        {"start": 60, "type": "1"},  # page 6
        {"start": 72, "type": "1"},  # page 7
        {"start": 84, "type": "1"},  # page 8
        {"start": 96, "type": "1"},  # page 9
        {"start": 108, "type": "1"}, # page 10
        {"start": 120, "type": "1"}, # page 11
        {"start": 132, "type": "1"}, # page 12
    ]
    
    for params in params_list:
        try:
            url = f"{catalog_url}?start={params['start']}&type={params['type']}"
            print(f"Scraping: {url}")
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Find all product rows
            rows = soup.select("tr.custom-table__body-row")
            if not rows:
                rows = soup.select(".product-catalogue-training-calendar__row")
            if not rows:
                # Try generic table rows
                rows = soup.select("table tbody tr")
            
            if not rows:
                print(f"  No rows found at offset {params['start']}, trying different selector...")
                # Try to find any assessment cards
                cards = soup.select("[data-course-id], .product-card, .catalogue-item")
                print(f"  Found {len(cards)} cards")
                if not cards and params['start'] > 0:
                    print("  Stopping pagination")
                    break
                continue
            
            print(f"  Found {len(rows)} rows")
            
            for row in rows:
                try:
                    # Get name and URL
                    link = row.select_one("a")
                    if not link:
                        continue
                    
                    name = link.get_text(strip=True)
                    href = link.get("href", "")
                    if href and not href.startswith("http"):
                        href = base_url + href
                    
                    # Get test types (A, B, K, P, C, S columns)
                    cols = row.select("td")
                    
                    remote_testing = False
                    adaptive = False
                    test_types = []
                    
                    # Parse columns for checkmarks
                    for i, col in enumerate(cols):
                        text = col.get_text(strip=True)
                        has_check = col.select_one("svg, img, .icon, [class*='check'], [class*='tick']")
                        if has_check or text in ["●", "✓", "✔", "yes"]:
                            if i == 1:
                                remote_testing = True
                            elif i == 2:
                                adaptive = True
                    
                    # Get test type badges
                    badges = row.select(".badge, [class*='type'], [class*='label']")
                    for badge in badges:
                        t = badge.get_text(strip=True).upper()
                        if t in ["A", "B", "K", "P", "C", "S"]:
                            test_types.append(t)
                    
                    if name and href:
                        assessment = {
                            "name": name,
                            "url": href,
                            "test_types": test_types,
                            "remote_testing": remote_testing,
                            "adaptive": adaptive,
                            "description": f"{name} is an SHL assessment."
                        }
                        all_assessments.append(assessment)
                        print(f"  Added: {name}")
                        
                except Exception as e:
                    print(f"  Error parsing row: {e}")
                    continue
            
            time.sleep(1)  # be polite to the server
            
        except Exception as e:
            print(f"Error fetching page: {e}")
            continue
    
    # If scraping didn't work well, use the known catalog
    if len(all_assessments) < 10:
        print("\nFalling back to known SHL catalog...")
        all_assessments = get_known_catalog()
    
    # Remove duplicates
    seen = set()
    unique = []
    for a in all_assessments:
        if a["name"] not in seen:
            seen.add(a["name"])
            unique.append(a)
    
    print(f"\nTotal assessments: {len(unique)}")
    
    with open("catalog.json", "w") as f:
        json.dump(unique, f, indent=2)
    
    print("Saved to catalog.json")
    return unique


def get_known_catalog():
    """
    Known SHL Individual Test Solutions catalog as fallback.
    Based on publicly available SHL product catalog.
    """
    return [
        {"name": "Verify Numerical Reasoning", "url": "https://www.shl.com/solutions/products/product-catalog/view/verify-numerical-reasoning/", "test_types": ["A"], "remote_testing": True, "adaptive": True, "description": "Verify Numerical Reasoning is an Ability test measuring numerical reasoning skills. Suitable for roles requiring data analysis, financial reasoning. Supports remote testing and adaptive format."},
        {"name": "Verify Verbal Reasoning", "url": "https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-reasoning/", "test_types": ["A"], "remote_testing": True, "adaptive": True, "description": "Verify Verbal Reasoning is an Ability test measuring verbal reasoning and comprehension. Supports remote testing and adaptive format."},
        {"name": "Verify Inductive Reasoning", "url": "https://www.shl.com/solutions/products/product-catalog/view/verify-inductive-reasoning/", "test_types": ["A"], "remote_testing": True, "adaptive": True, "description": "Verify Inductive Reasoning is an Ability test measuring logical and abstract reasoning skills. Supports remote testing and adaptive format."},
        {"name": "OPQ32r", "url": "https://www.shl.com/solutions/products/product-catalog/view/opq32r/", "test_types": ["P"], "remote_testing": True, "adaptive": False, "description": "OPQ32r (Occupational Personality Questionnaire) is a Personality assessment measuring 32 dimensions of workplace behavior and personality. Widely used for leadership, management, and professional roles."},
        {"name": "Motivational Questionnaire MQM5", "url": "https://www.shl.com/solutions/products/product-catalog/view/motivational-questionnaire-mqm5/", "test_types": ["P"], "remote_testing": True, "adaptive": False, "description": "Motivational Questionnaire MQM5 is a Personality/motivational assessment measuring what motivates and energizes employees at work."},
        {"name": "Java 8 (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/java-8-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Java 8 is a Knowledge test measuring Java programming skills including OOP, collections, streams, and concurrency. Suitable for mid to senior Java developers."},
        {"name": "Core Java (Advanced Level)", "url": "https://www.shl.com/solutions/products/product-catalog/view/core-java-advanced-level-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Core Java Advanced Level is a Knowledge test measuring advanced Java programming concepts for senior developers."},
        {"name": "Python (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/python-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Python is a Knowledge test measuring Python programming skills. Suitable for data engineers, backend developers, and data scientists."},
        {"name": "SQL (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/sql-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "SQL is a Knowledge test measuring database querying skills using SQL. Suitable for data analysts, backend developers, and database administrators."},
        {"name": "JavaScript (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/javascript-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "JavaScript is a Knowledge test measuring JavaScript programming skills for frontend and fullstack developers."},
        {"name": "Automata - Fix (JavaScript)", "url": "https://www.shl.com/solutions/products/product-catalog/view/automata-fix-javascript/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Automata Fix JavaScript is a coding simulation test where candidates fix broken JavaScript code. Tests real coding ability."},
        {"name": "Automata - Fix (Python)", "url": "https://www.shl.com/solutions/products/product-catalog/view/automata-fix-python/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Automata Fix Python is a coding simulation where candidates fix broken Python code. Tests real coding ability."},
        {"name": "Automata - Fix (Java)", "url": "https://www.shl.com/solutions/products/product-catalog/view/automata-fix-java/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Automata Fix Java is a coding simulation where candidates fix broken Java code. Tests real Java coding ability."},
        {"name": "Automata Pro", "url": "https://www.shl.com/solutions/products/product-catalog/view/automata-pro/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Automata Pro is an advanced coding simulation for software engineers. Tests real-world coding tasks across multiple languages."},
        {"name": "General Ability - Short Form", "url": "https://www.shl.com/solutions/products/product-catalog/view/general-ability-short-form/", "test_types": ["A"], "remote_testing": True, "adaptive": False, "description": "General Ability Short Form measures general cognitive ability including verbal, numerical, and abstract reasoning. Short duration for quick screening."},
        {"name": "Verify - Numerical Ability", "url": "https://www.shl.com/solutions/products/product-catalog/view/verify-numerical-ability/", "test_types": ["A"], "remote_testing": True, "adaptive": False, "description": "Verify Numerical Ability measures basic numerical skills for roles requiring everyday math and data interpretation."},
        {"name": "Verify - Verbal Ability", "url": "https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-ability-next-generation/", "test_types": ["A"], "remote_testing": True, "adaptive": False, "description": "Verify Verbal Ability measures language comprehension and verbal skills for customer-facing and administrative roles."},
        {"name": "Deductive Reasoning", "url": "https://www.shl.com/solutions/products/product-catalog/view/deductive-reasoning/", "test_types": ["A"], "remote_testing": True, "adaptive": False, "description": "Deductive Reasoning measures ability to draw logical conclusions from given information. Useful for analytical roles."},
        {"name": "Inductive Reasoning", "url": "https://www.shl.com/solutions/products/product-catalog/view/inductive-reasoning/", "test_types": ["A"], "remote_testing": True, "adaptive": False, "description": "Inductive Reasoning measures ability to identify patterns and rules from abstract information. Useful for technical and analytical roles."},
        {"name": "Numerical Reasoning", "url": "https://www.shl.com/solutions/products/product-catalog/view/numerical-reasoning/", "test_types": ["A"], "remote_testing": True, "adaptive": False, "description": "Numerical Reasoning measures ability to interpret and analyze numerical data. Used for finance, banking, and management roles."},
        {"name": "Verbal Reasoning", "url": "https://www.shl.com/solutions/products/product-catalog/view/verbal-reasoning/", "test_types": ["A"], "remote_testing": True, "adaptive": False, "description": "Verbal Reasoning measures ability to understand and analyze written information. Used for management and professional roles."},
        {"name": "Management and Graduate Item Bank", "url": "https://www.shl.com/solutions/products/product-catalog/view/management-and-graduate-item-bank/", "test_types": ["A"], "remote_testing": True, "adaptive": False, "description": "Management and Graduate Item Bank measures verbal, numerical, and inductive reasoning for graduate and management level candidates."},
        {"name": "Graduate Item Bank", "url": "https://www.shl.com/solutions/products/product-catalog/view/graduate-item-bank/", "test_types": ["A"], "remote_testing": True, "adaptive": False, "description": "Graduate Item Bank is an Ability test designed for graduate-level hiring, measuring reasoning across verbal and numerical domains."},
        {"name": "Operational Item Bank", "url": "https://www.shl.com/solutions/products/product-catalog/view/operational-item-bank/", "test_types": ["A"], "remote_testing": True, "adaptive": False, "description": "Operational Item Bank measures reasoning skills for operational and frontline roles."},
        {"name": "OPQ32", "url": "https://www.shl.com/solutions/products/product-catalog/view/opq32/", "test_types": ["P"], "remote_testing": True, "adaptive": False, "description": "OPQ32 is the full Occupational Personality Questionnaire measuring 32 personality dimensions critical for workplace success. Used for leadership and senior roles."},
        {"name": "Personality Questionnaire - Short Form", "url": "https://www.shl.com/solutions/products/product-catalog/view/short-form-opq/", "test_types": ["P"], "remote_testing": True, "adaptive": False, "description": "Short Form OPQ is a shorter personality assessment measuring key personality traits for workplace behavior. Quick to complete."},
        {"name": "Universal Competency Framework", "url": "https://www.shl.com/solutions/products/product-catalog/view/universal-competency-framework/", "test_types": ["P"], "remote_testing": True, "adaptive": False, "description": "Universal Competency Framework measures behavioral competencies aligned to job performance across all levels."},
        {"name": "Sales Preference Questionnaire", "url": "https://www.shl.com/solutions/products/product-catalog/view/sales-preference-questionnaire/", "test_types": ["P"], "remote_testing": True, "adaptive": False, "description": "Sales Preference Questionnaire measures motivations and preferences specific to sales roles. Ideal for sales hiring."},
        {"name": "Customer Contact Styles Questionnaire", "url": "https://www.shl.com/solutions/products/product-catalog/view/customer-contact-styles-questionnaire/", "test_types": ["P"], "remote_testing": True, "adaptive": False, "description": "Customer Contact Styles Questionnaire measures styles and preferences for customer-facing and contact center roles."},
        {"name": "Team Styles Questionnaire", "url": "https://www.shl.com/solutions/products/product-catalog/view/team-styles-questionnaire/", "test_types": ["P"], "remote_testing": True, "adaptive": False, "description": "Team Styles Questionnaire measures preferred working styles within teams. Useful for team building and collaborative roles."},
        {"name": "Work Styles Questionnaire", "url": "https://www.shl.com/solutions/products/product-catalog/view/work-styles-questionnaire/", "test_types": ["P"], "remote_testing": True, "adaptive": False, "description": "Work Styles Questionnaire measures individual working preferences and styles relevant to job performance."},
        {"name": "Technology Profession Apprentice (Entry Level)", "url": "https://www.shl.com/solutions/products/product-catalog/view/technology-profession-apprentice/", "test_types": ["A", "K"], "remote_testing": True, "adaptive": False, "description": "Technology Profession Apprentice measures aptitude and knowledge for entry-level technology roles including IT support."},
        {"name": "Microsoft Excel (Office 2013)", "url": "https://www.shl.com/solutions/products/product-catalog/view/microsoft-excel-2013/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Microsoft Excel test measures proficiency in Excel for administrative and data roles."},
        {"name": "Microsoft Word (Office 2013)", "url": "https://www.shl.com/solutions/products/product-catalog/view/microsoft-word-2013/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Microsoft Word test measures document creation and formatting skills for administrative roles."},
        {"name": "Basic Computer Literacy Skills", "url": "https://www.shl.com/solutions/products/product-catalog/view/basic-computer-literacy-skills/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Basic Computer Literacy Skills measures fundamental computer skills for entry-level roles requiring PC usage."},
        {"name": "Occupational Personality Questionnaire (OPQ) - Leadership Report", "url": "https://www.shl.com/solutions/products/product-catalog/view/opq-leadership-report/", "test_types": ["P"], "remote_testing": True, "adaptive": False, "description": "OPQ Leadership Report uses personality data to assess leadership potential and style. Used for senior and executive hiring."},
        {"name": "Situational Judgement Test", "url": "https://www.shl.com/solutions/products/product-catalog/view/situational-judgement/", "test_types": ["B"], "remote_testing": True, "adaptive": False, "description": "Situational Judgement Test measures judgment and decision making in realistic workplace scenarios."},
        {"name": "MQ Motivation Questionnaire", "url": "https://www.shl.com/solutions/products/product-catalog/view/mq-motivation-questionnaire/", "test_types": ["P"], "remote_testing": True, "adaptive": False, "description": "MQ Motivation Questionnaire identifies what motivates candidates at work. Useful for retention and role fit."},
        {"name": "Workplace Safety Solutions", "url": "https://www.shl.com/solutions/products/product-catalog/view/workplace-safety-solutions/", "test_types": ["B"], "remote_testing": True, "adaptive": False, "description": "Workplace Safety Solutions measures safety awareness and behaviors for roles in industrial, manufacturing, and operational environments."},
        {"name": "Dependability & Safety Instrument", "url": "https://www.shl.com/solutions/products/product-catalog/view/dependability-safety-instrument/", "test_types": ["P"], "remote_testing": True, "adaptive": False, "description": "Dependability and Safety Instrument measures reliability, integrity and safety behaviors for frontline and operational roles."},
        {"name": "Advanced Verify Numerical Reasoning", "url": "https://www.shl.com/solutions/products/product-catalog/view/advanced-verify-numerical-reasoning/", "test_types": ["A"], "remote_testing": True, "adaptive": True, "description": "Advanced Verify Numerical Reasoning is a high-difficulty numerical reasoning test for senior management and financial roles."},
        {"name": "Advanced Verify Verbal Reasoning", "url": "https://www.shl.com/solutions/products/product-catalog/view/advanced-verify-verbal-reasoning/", "test_types": ["A"], "remote_testing": True, "adaptive": True, "description": "Advanced Verify Verbal Reasoning is a high-difficulty verbal reasoning test for senior and executive-level roles."},
        {"name": "Agile Methodology (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/agile-methodology-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Agile Methodology test measures knowledge of agile practices, scrum, kanban for software development roles."},
        {"name": "C# (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/c-sharp-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "C# test measures .NET and C# programming skills for software developer roles."},
        {"name": "C++ (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/c-plus-plus-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "C++ test measures C++ programming skills for systems, embedded, and software engineering roles."},
        {"name": "Data Analysis", "url": "https://www.shl.com/solutions/products/product-catalog/view/data-analysis/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Data Analysis test measures ability to interpret data, draw insights, and make data-driven decisions. Suitable for analyst roles."},
        {"name": "Machine Learning (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/machine-learning-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Machine Learning test measures knowledge of ML algorithms, model training, and evaluation for data science roles."},
        {"name": "R (Programming)", "url": "https://www.shl.com/solutions/products/product-catalog/view/r-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "R Programming test measures proficiency in R for statistical analysis and data science roles."},
        {"name": "Scala (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/scala-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Scala test measures Scala programming skills for big data and functional programming roles."},
        {"name": "Spring Framework", "url": "https://www.shl.com/solutions/products/product-catalog/view/spring-framework/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Spring Framework test measures knowledge of the Spring ecosystem for Java backend developers."},
        {"name": "ReactJS (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/reactjs-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "ReactJS test measures frontend development skills in React for UI and fullstack developers."},
        {"name": "Angular", "url": "https://www.shl.com/solutions/products/product-catalog/view/angular/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Angular test measures frontend framework skills for web developers building enterprise applications."},
        {"name": "Node.js (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/node-js-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Node.js test measures server-side JavaScript skills for backend and fullstack developers."},
        {"name": "AWS (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/aws-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "AWS test measures knowledge of Amazon Web Services for cloud engineers and DevOps roles."},
        {"name": "Cyber Security (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/cyber-security-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Cyber Security test measures knowledge of security principles, threats, and practices for IT security roles."},
        {"name": "Accounting and Finance Fundamentals (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/accounting-and-finance-fundamentals-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Accounting and Finance Fundamentals measures knowledge of financial principles, bookkeeping, and reporting for finance roles."},
        {"name": "Financial Accounting (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/financial-accounting-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Financial Accounting test measures accounting knowledge for accountants and finance professionals."},
        {"name": "Business Analysis Fundamentals", "url": "https://www.shl.com/solutions/products/product-catalog/view/business-analysis-fundamentals/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Business Analysis Fundamentals measures requirements gathering, analysis, and documentation skills for BA roles."},
        {"name": "Project Management (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/project-management-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Project Management test measures knowledge of project planning, execution, and delivery for PM roles."},
        {"name": "SAP ERP (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/sap-erp-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "SAP ERP test measures knowledge of SAP enterprise systems for ERP consultants and administrators."},
        {"name": "Salesforce (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/salesforce-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Salesforce test measures CRM knowledge and platform skills for Salesforce administrators and developers."},
        {"name": "Digital Marketing (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/digital-marketing-new/", "test_types": ["K"], "remote_testing": True, "adaptive": False, "description": "Digital Marketing test measures knowledge of SEO, SEM, social media, and digital campaign management."},
        {"name": "General Sales Aptitude", "url": "https://www.shl.com/solutions/products/product-catalog/view/general-sales-aptitude/", "test_types": ["B"], "remote_testing": True, "adaptive": False, "description": "General Sales Aptitude measures natural sales ability, persuasion, and customer engagement skills for sales roles."},
        {"name": "Customer Service Simulation", "url": "https://www.shl.com/solutions/products/product-catalog/view/customer-service-simulation/", "test_types": ["B"], "remote_testing": True, "adaptive": False, "description": "Customer Service Simulation measures how candidates handle real customer service scenarios. For contact center and support roles."},
        {"name": "Verify Interactive - Deductive", "url": "https://www.shl.com/solutions/products/product-catalog/view/verify-interactive-deductive/", "test_types": ["A"], "remote_testing": True, "adaptive": True, "description": "Verify Interactive Deductive is an adaptive deductive reasoning test with interactive items for professional and graduate hiring."},
        {"name": "Verify Interactive - Inductive", "url": "https://www.shl.com/solutions/products/product-catalog/view/verify-interactive-inductive/", "test_types": ["A"], "remote_testing": True, "adaptive": True, "description": "Verify Interactive Inductive is an adaptive inductive/abstract reasoning test for professional and graduate level hiring."},
        {"name": "Verify Interactive - Numerical", "url": "https://www.shl.com/solutions/products/product-catalog/view/verify-interactive-numerical/", "test_types": ["A"], "remote_testing": True, "adaptive": True, "description": "Verify Interactive Numerical is an adaptive numerical reasoning test with interactive items for professional hiring."},
    ]


if __name__ == "__main__":
    results = scrape_shl_catalog()
    print(f"\nDone! {len(results)} assessments saved to catalog.json")