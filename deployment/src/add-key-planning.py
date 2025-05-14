import os
import yaml
from glob import glob
from pprint import pprint

def open_yaml(file_path):
    """Ouvre un fichier YAML et retourne son contenu sous forme de dictionnaire."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(file_path, content):
    """Sauvegarde un dictionnaire dans un fichier YAML."""
    with open(file_path, 'w') as f:
        yaml.dump(content, f, sort_keys=False, default_flow_style=False)

def determine_bootcamp_type(topic):
    """Détermine le type de bootcamp en fonction du topic."""
    if topic and isinstance(topic, str):
        if "cyber" in topic.lower() or "data" in topic.lower():
            return "normal"
    return "upskilling"

def calculate_total_halfdays(children_files):
    """Calcule le nombre total de demi-journées basé sur les fichiers des enfants."""
    total = 0
    print("\nCALCUL DES DEMI-JOURNÉES:")
    print("-" * 40)
    for file_path in children_files:
        child_content = open_yaml(file_path)
        halfdays = child_content.get("halfDays", 0)
        print(f"Fichier: {os.path.basename(file_path)}, halfDays: {halfdays}")
        total += halfdays
    print(f"Total des demi-journées: {total}")
    print("-" * 40)
    return total

def calculate_total_evening(children_files):
    """Calcule le nombre total de soirées basé sur les fichiers des enfants."""
    total = 0
    print("\nCALCUL DES SOIRÉES:")
    print("-" * 40)
    for file_path in children_files:
        child_content = open_yaml(file_path)
        evening = child_content.get("evening", 0)
        print(f"Fichier: {os.path.basename(file_path)}, evening: {evening}")
        total += evening
    print(f"Total des soirées: {total}")
    print("-" * 40)
    return total

def determine_total_masterclass(path_level, bootcamp_type):
    """Détermine le nombre total de masterclass en fonction du niveau du parcours et du type de bootcamp."""
    if bootcamp_type == "upskilling":
        return 3
    
    if path_level == "essentials":
        return 3
    elif path_level == "fullstack":
        return 11
    elif path_level == "lead":
        return 5
    
    return 0

def calculate_hours(bootcamp_type, total_halfdays, total_evening):
    """Calcule le nombre total d'heures en fonction du type de bootcamp et des demi-journées/soirées."""
    if bootcamp_type == "normal":
        return total_halfdays * 3.75
    else:
        return total_halfdays * 3.75 + total_evening * 5

def determine_rhythm(halfdays, is_fulltime, bootcamp_type, title, slug=''):
    """Détermine le rythme en fonction des demi-journées et du mode (full-time/part-time)."""
    if halfdays == 0:
        return "noWorkingDay"
    
    # Vérifier si le titre ou le slug contient "project" ou "netflix"
    title_lower = title.lower() if title else ""
    slug_lower = slug.lower() if slug else ""
    
    # Si c'est un bootcamp upskilling et qu'il y a "project" ou "netflix" dans le titre ou le slug
    if bootcamp_type == "upskilling" and (
        "project" in title_lower or 
        "netflix" in title_lower or 
        "project" in slug_lower or 
        "netflix" in slug_lower
    ):
        return "evening"
    
    if is_fulltime:
        return "dayFullTime"
    else:
        return "dayMasterclass"

def create_timeslots(rhythm):
    """Crée les créneaux horaires en fonction du rythme."""
    if rhythm == "noWorkingDay":
        return []
    
    if rhythm == "dayFullTime":
        return [
            {"start": "09:30", "end": "12:30"},
            {"start": "13:30", "end": "18:30"}
        ]
    
    if rhythm == "dayMasterclass":
        return [{"start": "10:00", "end": "18:00"}]
    
    if rhythm == "evening":
        return [{"start": "18:00", "end": "20:30"}]
    
    return []

def create_program_item(child_slug, child_content, is_fulltime, bootcamp_type):
    """Crée un élément de programme pour un enfant donné."""
    title = child_content.get("title", child_slug)
    halfdays = child_content.get("halfDays", 0)
    
    rhythm = determine_rhythm(halfdays, is_fulltime, bootcamp_type, title, child_slug)
    timeslots = create_timeslots(rhythm)
    
    return {
        "slug": child_slug,
        "title": title,
        "halfDays": halfdays,
        "rhythm": rhythm,
        "timeSlots": timeslots
    }

def create_planning_structure(tree_content, children_files, children_content):
    """Crée la structure planning à partir du contenu de l'arbre et des fichiers des enfants."""
    # Déterminer le type de bootcamp
    bootcamp_type = determine_bootcamp_type(tree_content.get("topic", ""))
    print(f"\nBOOTCAMP TYPE: {bootcamp_type}")
    print(f"Topic: {tree_content.get('topic', 'Non défini')}")
    
    # Déterminer le nombre total de demi-journées
    # Si halfDays est défini dans root.yaml, l'utiliser
    # Sinon, calculer la somme des halfDays des enfants
    if "halfDays" in tree_content:
        total_halfdays = tree_content["halfDays"]
    else:
        # Calculer la somme des halfDays des enfants
        total_halfdays = 0
        for file_path in children_files:
            child_content = open_yaml(file_path)
            total_halfdays += child_content.get("halfDays", 0)
    
    # Compter les soirées (modules avec rythme "evening")
    evening_count = 0
    for child_slug, child_content in children_content.items():
        title = child_content.get("title", child_slug)
        halfdays = child_content.get("halfDays", 0)
        
        # Vérifier si le module est un evening
        if bootcamp_type == "upskilling" and (
            "project" in title.lower() or 
            "netflix" in title.lower() or 
            "project" in child_slug.lower() or 
            "netflix" in child_slug.lower()
        ) and halfdays > 0:
            evening_count += 1
    
    total_evening = evening_count
    number_of_modules = len(tree_content.get("children", []))
    total_masterclass = determine_total_masterclass(tree_content.get("pathLevel", ""), bootcamp_type)
    print(f"PathLevel: {tree_content.get('pathLevel', 'Non défini')}, totalMasterclass: {total_masterclass}")
    
    # Calculer les heures
    hours = total_halfdays * 3.75 + total_evening * 5
    
    # Calculer les jours et semaines
    days = total_halfdays // 2 if total_halfdays > 0 else 0
    weeks = days // 5 if days > 0 else 0
    
    # S'assurer que les jours et semaines sont au moins 1
    days = max(1, days)
    weeks = max(1, weeks)
    
    print(f"\nRÉSUMÉ DES CALCULS:")
    print(f"Total halfDays: {total_halfdays}")
    print(f"Total evening: {total_evening}")
    print(f"Nombre de modules: {number_of_modules}")
    print(f"Heures: {hours}")
    print(f"Jours: {days}")
    print(f"Semaines: {weeks}")
    
    # Créer le programme full-time
    program_fulltime = []
    for child_slug, child_content in children_content.items():
        program_item = create_program_item(child_slug, child_content, True, bootcamp_type)
        program_fulltime.append(program_item)
    
    # Créer le programme part-time
    program_parttime = []
    for child_slug, child_content in children_content.items():
        program_item = create_program_item(child_slug, child_content, False, bootcamp_type)
        program_parttime.append(program_item)
    
    # Créer la structure planning
    planning = {
        "bootcampType": bootcamp_type,
        "durationBootcamp": {
            "weeks": weeks,
            "days": days,
            "hours": hours,
            "numberOfModule": number_of_modules,
            "totalHalfDays": total_halfdays,
            "totalEvening": total_evening,
            "totalMasterclass": total_masterclass,
        },
        "schedule": {
            "full-time": {
                "program": program_fulltime
            },
            "part-time": {
                "program": program_parttime
            }
        }
    }
    
    return planning

def add_planning_to_yaml(repository_path):
    """Ajoute la structure planning à tous les fichiers root.yaml."""
    root_files = glob(os.path.join(repository_path, "**", "root.yaml"), recursive=True)
    
    if not root_files:
        print(f"Aucun fichier root.yaml trouvé dans {repository_path}")
        return 0
    
    print(f"Nombre de fichiers root.yaml trouvés : {len(root_files)}")
    
    modified_files = 0
    
    for root_file in root_files:
        print(f"\n{'=' * 80}")
        print(f"FICHIER ROOT : {root_file}")
        print(f"{'=' * 80}")
        
        # Lire le contenu du fichier root.yaml
        tree_content = open_yaml(root_file)
        
        # Afficher le contenu complet du fichier
        print("\nCONTENU COMPLET DU FICHIER ROOT.YAML :")
        print("-" * 40)
        pprint(tree_content, width=120, sort_dicts=False)
        print("-" * 40)
        
        # Vérifier si la clé planning existe déjà
        if "planning" in tree_content:
            print(f"La clé planning existe déjà dans {root_file}, elle sera remplacée")
            # On continue l'exécution sans faire de continue
        
        # Trouver les fichiers YAML des enfants et leur contenu
        children_files = []
        children_content = {}
        if "children" in tree_content and isinstance(tree_content["children"], list):
            print("\nDÉTAILS DES FICHIERS ENFANTS :")
            print("-" * 40)
            for child_slug in tree_content["children"]:
                # Rechercher les fichiers .yaml et .yml
                yaml_files = glob(os.path.join(repository_path, "**", f"{child_slug}.yaml"), recursive=True)
                yml_files = glob(os.path.join(repository_path, "**", f"{child_slug}.yml"), recursive=True)
                
                all_files = yaml_files + yml_files
                
                if all_files:
                    file_path = all_files[0]
                    children_files.append(file_path)
                    child_content = open_yaml(file_path)
                    children_content[child_slug] = child_content
                    print(f"Fichier enfant: {file_path}")
                    print(f"Contenu du fichier {child_slug}:")
                    pprint(child_content, width=120, sort_dicts=False)
                    print("-" * 40)
                else:
                    print(f"Aucun fichier trouvé pour l'enfant: {child_slug}")
                    print("-" * 40)
        
        # Créer la structure planning
        planning = create_planning_structure(tree_content, children_files, children_content)
        
        # Ajouter la structure planning au contenu
        tree_content["planning"] = planning
        
        # Afficher la structure planning créée
        print("\nSTRUCTURE PLANNING CRÉÉE :")
        print("-" * 40)
        pprint(planning, width=120, sort_dicts=False)
        print("-" * 40)
        
        # Sauvegarder le fichier modifié
        save_yaml(root_file, tree_content)
        print(f"Planning ajouté au fichier {root_file}")
        modified_files += 1
    
    print(f"\nNombre de fichiers modifiés : {modified_files}")
    return modified_files

if __name__ == "__main__":
    repository_path = os.getenv("GITHUB_WORKSPACE", ".")
    print(f"Recherche des fichiers root.yaml dans : {repository_path}")
    add_planning_to_yaml(repository_path)