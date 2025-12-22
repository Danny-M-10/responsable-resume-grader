"""
Skills Researcher Module
Finds equivalent job titles, skills synonyms, and certification alternatives
"""

from typing import List, Dict


class SkillsResearcher:
    """
    Research equivalent terms for job titles, skills, and certifications
    Uses built-in knowledge base of common equivalents
    """

    def __init__(self):
        # Job title equivalents database
        self.title_equivalents = {
            'data scientist': [
                'Senior Data Scientist', 'Data Analyst', 'Machine Learning Engineer',
                'ML Engineer', 'AI Scientist', 'Research Scientist', 'Data Science Engineer',
                'Applied Scientist', 'Analytics Engineer'
            ],
            'software engineer': [
                'Software Developer', 'Application Developer', 'Programmer',
                'Senior Software Engineer', 'Full Stack Developer', 'Backend Developer',
                'Frontend Developer', 'Software Development Engineer', 'SDE'
            ],
            'data engineer': [
                'Data Pipeline Engineer', 'ETL Developer', 'Big Data Engineer',
                'Data Infrastructure Engineer', 'Analytics Engineer', 'Data Platform Engineer'
            ],
            'product manager': [
                'Senior Product Manager', 'Technical Product Manager', 'Product Owner',
                'Associate Product Manager', 'Group Product Manager', 'Principal Product Manager'
            ],
            'machine learning engineer': [
                'ML Engineer', 'Data Scientist', 'AI Engineer', 'Applied Scientist',
                'Research Engineer', 'Deep Learning Engineer', 'NLP Engineer'
            ],
            'devops engineer': [
                'Site Reliability Engineer', 'SRE', 'Platform Engineer',
                'Infrastructure Engineer', 'Cloud Engineer', 'Systems Engineer'
            ],
            'business analyst': [
                'Data Analyst', 'Systems Analyst', 'Business Intelligence Analyst',
                'Analytics Consultant', 'Functional Analyst', 'Requirements Analyst'
            ],
            'project manager': [
                'Program Manager', 'Technical Project Manager', 'Delivery Manager',
                'Scrum Master', 'Agile Project Manager', 'PMO'
            ]
        }

        # Skill synonyms database
        self.skill_synonyms = {
            'python': ['Python3', 'Python 2', 'Python 3', 'py'],
            'javascript': ['JS', 'ECMAScript', 'ES6', 'ES2015', 'Node.js'],
            'machine learning': ['ML', 'statistical learning', 'predictive modeling', 'AI'],
            'deep learning': ['DL', 'neural networks', 'deep neural networks', 'DNN'],
            'natural language processing': ['NLP', 'text mining', 'language understanding'],
            'aws': ['Amazon Web Services', 'Amazon AWS', 'AWS Cloud'],
            'azure': ['Microsoft Azure', 'Azure Cloud', 'MS Azure'],
            'gcp': ['Google Cloud Platform', 'Google Cloud', 'GCP'],
            'kubernetes': ['k8s', 'container orchestration'],
            'docker': ['containerization', 'containers'],
            'sql': ['Structured Query Language', 'relational databases', 'RDBMS'],
            'nosql': ['non-relational databases', 'document databases'],
            'react': ['React.js', 'ReactJS'],
            'angular': ['Angular.js', 'AngularJS'],
            'node.js': ['Node', 'NodeJS'],
            'git': ['version control', 'source control', 'GitHub', 'GitLab'],
            'agile': ['Scrum', 'agile methodologies', 'iterative development'],
            'ci/cd': ['continuous integration', 'continuous deployment', 'DevOps pipeline'],
            'rest api': ['RESTful API', 'REST', 'web services', 'API'],
            'microservices': ['microservice architecture', 'service-oriented architecture', 'SOA'],
            'tensorflow': ['TF', 'TensorFlow 2'],
            'pytorch': ['PyTorch', 'torch'],
            'scikit-learn': ['sklearn', 'scikit learn'],
            'data visualization': ['dataviz', 'charts', 'dashboards', 'reporting'],
            'tableau': ['Tableau Desktop', 'Tableau Server'],
            'power bi': ['PowerBI', 'Microsoft Power BI'],
            'spark': ['Apache Spark', 'PySpark'],
            'hadoop': ['Apache Hadoop', 'HDFS', 'MapReduce'],
            'mongodb': ['Mongo', 'MongoDB Atlas'],
            'postgresql': ['Postgres', 'PostgreSQL'],
            'mysql': ['MySQL', 'MariaDB']
        }

        # Certification equivalents
        self.cert_equivalents = {
            'aws certified solutions architect': [
                'AWS Solutions Architect', 'AWS CSA', 'AWS SA'
            ],
            'aws certified machine learning': [
                'AWS ML', 'AWS Machine Learning Specialty'
            ],
            'google cloud professional data engineer': [
                'GCP Data Engineer', 'Google Data Engineer'
            ],
            'microsoft certified azure': [
                'Azure Certification', 'MS Azure Certified'
            ],
            'pmp': [
                'Project Management Professional', 'PMI PMP'
            ],
            'cissp': [
                'Certified Information Systems Security Professional'
            ],
            'comptia security+': [
                'Security Plus', 'CompTIA Security Plus'
            ]
        }

    def find_equivalent_titles(self, job_title: str, experience_level: str = "") -> List[str]:
        """
        Find equivalent job titles

        Args:
            job_title: The job title to find equivalents for
            experience_level: Optional experience level ("Junior", "Mid", "Senior") to filter seniority variations

        Returns:
            List of equivalent titles
        """
        job_title_lower = job_title.lower()

        # Check exact match
        if job_title_lower in self.title_equivalents:
            equivalents = self.title_equivalents[job_title_lower].copy()
        else:
            # Check partial matches
            equivalents = []
            for key, values in self.title_equivalents.items():
                if key in job_title_lower or job_title_lower in key:
                    equivalents.extend(values)

        # Add variations with seniority levels (filtered by experience level)
        base_variations = self._generate_seniority_variations(job_title, experience_level)
        equivalents.extend(base_variations)

        return list(set(equivalents))  # Remove duplicates

    def find_skill_synonyms(self, skill: str) -> List[str]:
        """
        Find synonyms for a skill

        Args:
            skill: The skill to find synonyms for

        Returns:
            List of synonyms
        """
        skill_lower = skill.lower()

        # Check exact match
        if skill_lower in self.skill_synonyms:
            return self.skill_synonyms[skill_lower]

        # Check partial matches
        synonyms = []
        for key, values in self.skill_synonyms.items():
            if key in skill_lower or skill_lower in key:
                synonyms.extend(values)

        return list(set(synonyms))

    def find_cert_equivalents(self, certification: str) -> List[str]:
        """
        Find equivalent certifications

        Args:
            certification: The certification to find equivalents for

        Returns:
            List of equivalent certifications
        """
        cert_lower = certification.lower()

        # Check exact match
        if cert_lower in self.cert_equivalents:
            return self.cert_equivalents[cert_lower]

        # Check partial matches
        equivalents = []
        for key, values in self.cert_equivalents.items():
            if key in cert_lower or cert_lower in key:
                equivalents.extend(values)

        return list(set(equivalents))

    def _generate_seniority_variations(self, title: str, experience_level: str = "") -> List[str]:
        """
        Generate variations with different seniority levels, filtered by experience level
        
        Args:
            title: The job title to generate variations for
            experience_level: Optional experience level to filter variations ("Junior", "Mid", "Senior")
        
        Returns:
            List of seniority variations, filtered based on experience_level
        """
        variations = []

        # Remove existing seniority markers
        base_title = title
        seniority_markers = ['senior', 'sr.', 'junior', 'jr.', 'lead', 'principal', 'staff']

        for marker in seniority_markers:
            base_title = base_title.lower().replace(marker, '').strip()

        # Normalize experience level for comparison
        exp_level_lower = experience_level.lower().strip() if experience_level else ""

        # Filter variations based on experience level
        if exp_level_lower == "senior":
            # For Senior roles: exclude Junior variations
            variations.append(f"Senior {base_title.title()}")
            variations.append(f"Lead {base_title.title()}")
            variations.append(f"Principal {base_title.title()}")
        elif exp_level_lower == "junior":
            # For Junior roles: exclude Senior, Lead, Principal variations
            variations.append(f"Junior {base_title.title()}")
        elif exp_level_lower == "mid" or exp_level_lower == "":
            # For Mid-level or unspecified: include all variations
            variations.append(f"Senior {base_title.title()}")
            variations.append(f"Junior {base_title.title()}")
            variations.append(f"Lead {base_title.title()}")
            variations.append(f"Principal {base_title.title()}")
        else:
            # Unknown experience level: include all variations
            variations.append(f"Senior {base_title.title()}")
            variations.append(f"Junior {base_title.title()}")
            variations.append(f"Lead {base_title.title()}")
            variations.append(f"Principal {base_title.title()}")

        return variations
