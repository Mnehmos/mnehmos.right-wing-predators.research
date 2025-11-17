#!/usr/bin/env python3
"""Update enrichments for batch 3 part 1 (IDs 922-950) with researched data"""

import json

# Updates to apply - keyed by ID
updates = {
    922: {
        "name": "Robert Fenton",
        "year": 2024,
        "description": "Robert Fenton, 55, youth pastor at Abide In the Vine Fellowship in Owego, New York, in the late 1990s, was arrested in April 2024 after attempting to flee from Brisbane, Australia to the Philippines. He had told a 14-year-old girl's parents he was 'meant to be with her,' and with church leaders' approval, conducted a 'courtship' under strict conditions. Fenton frequently assaulted the underage girl during his two years at the church. He pleaded guilty to aggravated indecent assault and statutory sexual assault, both second-degree felonies, and was sentenced to 6 to 12 years in prison.",
        "crime": ["sexual assault", "indecent assault"],
        "position": ["youth pastor"],
        "tags": ["church abuse", "child abuse", "grooming", "international fugitive"]
    },
    923: {
        "name": "Joshua Burton Henley",
        "year": 2021,
        "description": "Joshua Burton Henley, 32, a youth minister at Washington Avenue Church of Christ in Evansville, Indiana, was arrested in June 2021 while driving a victim back to Tennessee. He had multiple victims between ages 12 and 16 in at least three states. Investigation revealed he communicated with and requested photographs from approximately 20-25 juveniles ages 14-17. He was sentenced to 45 years in federal prison on eight convictions including producing sexually explicit images of minors, transporting and possessing child pornography, and transporting a minor across state lines for sexual activity.",
        "crime": ["child pornography", "online solicitation", "sexual trafficking"],
        "position": ["youth minister"],
        "tags": ["church abuse", "child abuse", "online exploitation"]
    },
    924: {
        "name": "Ronnie Lee Barron",
        "year": 2021,
        "description": "Ronnie Lee Barron, 44, youth pastor at Loris First Presbyterian Church and volunteer baseball coach at Loris High School in South Carolina, was arrested in December 2021 for an inappropriate relationship with a minor. During the 2020-2021 school year, Barron engaged in sexual contact with a 16-17 year-old student. He was charged with third-degree sexual exploitation of a minor and sexual battery with a student. He pled guilty and was sentenced to eight years in prison suspended to probation.",
        "crime": ["sexual exploitation", "sexual battery"],
        "position": ["youth pastor", "sports coach"],
        "tags": ["church abuse", "child abuse", "school predator"]
    },
    925: {
        "name": "Donald Courtney Biggs",
        "year": 2018,
        "description": "Donald Courtney Biggs, youth pastor at Medford church (MTN Church) in Oregon, was arrested in 2015 on multiple counts of child pornography. He secretly recorded dozens of minor church members in various stages of undress during church events and trips. Biggs pleaded guilty in 2018 to transporting with intent to engage in criminal sexual activity and was sentenced to 15 years in federal prison at Federal Correctional Institution in Sandstone, Minnesota.",
        "crime": ["child pornography", "secret recording of minors"],
        "position": ["youth pastor"],
        "tags": ["church abuse", "child abuse", "voyeurism"]
    },
    926: {
        "name": "Ben Courson",
        "year": 2021,
        "description": "Ben Courson, 33, pastor of Applegate Christian Fellowship in Jacksonville, Oregon, announced in August 2021 that he would take a leave of absence following allegations of sexual misconduct from three former female church members. A fourth woman filed a police report for sexual assault, which was under investigation. Courson admitted to inappropriate sexual activity with multiple women and church elders stated he was disqualified from pastoral role. Despite resigning, Courson later returned to ministry posting motivational videos and preaching at youth venues.",
        "crime": ["sexual misconduct", "sexual assault allegations"],
        "position": ["pastor"],
        "tags": ["church abuse", "allegations", "megachurch"]
    },
    927: {
        "name": "Jon Courson",
        "year": 2021,
        "description": "Jon Courson, founder of Applegate Christian Fellowship near Medford, Oregon, had allegations that he engaged in an inappropriate romantic relationship with a female staff member in the 1980s. Seminary professors and former church members reported that Applegate leaders knew of the relationship but refused to discipline Courson, keeping his sin private. Courson retired in 2020 but maintains a radio ministry called Searchlight. Multiple allegations surface regarding his control of staff, church members, and church finances.",
        "crime": ["sexual misconduct allegations"],
        "position": ["pastor", "founder"],
        "tags": ["church abuse", "allegations", "cover-up", "megachurch"]
    },
    935: {
        "name": "Kevin Etherington",
        "year": 2022,
        "description": "Kevin Etherington, Assistant District Attorney in Payne and Logan counties, Oklahoma, was arrested in November 2022 and charged with child pornography possession. The Oklahoma State Bureau of Investigation's ICAC unit received cybertips of suspected child sexual abuse material on his Google Drive account and discovered at least 153 videos, screenshots, and photos of prepubescent girls being sexually abused. Etherington faced one count of aggravated possession of child pornography and one count of peeping tom felony after evidence emerged of voyeuristic photographs of children.",
        "crime": ["child pornography", "voyeurism"],
        "position": ["assistant district attorney"],
        "tags": ["government official", "child abuse", "law enforcement predator"]
    },
    940: {
        "name": "Samuel Rappylee Bateman",
        "year": 2023,
        "description": "Samuel Rappylee Bateman, 47, of Colorado City, Arizona, former FLDS member who broke away to found his own offshoot group, was arrested in Flagstaff, Arizona in August 2022 after officers found three girls aged 11-14 in an unventilated trailer. Bateman took at least 20 wives, most minors, and punished followers who did not treat him as a prophet. He was indicted in May 2023 on charges relating to a years-long conspiracy to amass 'wives' including minors across state lines. Sentenced to 50 years in prison.",
        "crime": ["child abuse", "sexual trafficking", "polygamy"],
        "position": ["FLDS offshoot leader", "self-proclaimed prophet"],
        "tags": ["FLDS", "polygamy", "child trafficking", "cult"]
    },
    941: {
        "name": "Jonathan Ryan Ensey",
        "year": 2022,
        "description": "Jonathan Ryan Ensey, 37, music director at Living Way Church in Conroe, Texas (son of the pastor), was found guilty of grooming a minor in March 2022. While serving as music director in August 2019, he kissed and fondled an underage girl he had known since she was 9 years old. Ensey sent her multiple nude photos, sexually explicit messages, and expressed wanting to 'hurt' her. Sentenced to concurrent four years for indecency with a child and eight years for online solicitation of a minor.",
        "crime": ["child sexual abuse", "online solicitation"],
        "position": ["music director", "church leader"],
        "tags": ["church abuse", "child abuse", "grooming"]
    },
    942: {
        "name": "Conrad Estrada Valdez",
        "year": 2021,
        "description": "Conrad Estrada Valdez, 61, pastor at The Restoration Outreach Christian Church in Houston, Texas, pleaded guilty in 2021 to sexual assault of a child between ages 14 and 17. In 2019, a then-30-year-old woman disclosed that Valdez had sexually abused her when she was 15. She described him as a longtime family friend and pastor/mentor. She had initially sought counseling from him after experiencing previous sexual assault. Valdez was sentenced to 14 years in prison.",
        "crime": ["sexual assault of child"],
        "position": ["pastor"],
        "tags": ["church abuse", "child abuse", "counselor exploitation"]
    },
    943: {
        "name": "Aaron Duane Shipman",
        "year": 2022,
        "description": "Aaron Duane Shipman, 44, former lead pastor at Bible Baptist Church in Odessa, Texas, was arrested in January 2022 and charged with second-degree felony sexual assault. A young woman filed a police report claiming Shipman had sexually assaulted her multiple times over the preceding two years when she was a minor. She reported at least three sexual intercourse incidents, with the most recent occurring just one day before her report. Church officials fired Shipman immediately.",
        "crime": ["sexual assault"],
        "position": ["pastor"],
        "tags": ["church abuse", "child abuse", "Baptist"]
    },
    945: {
        "name": "Sergio David Bezerra",
        "year": 2007,
        "description": "Sergio David Bezerra, teacher at Waco Baptist Academy, was arrested in 2007 on indecency with a child charges after two fourth-grade girls reported abuse. Bezerra had taught Spanish and Latin at the school for 13 years before resigning months before arrest. The girls testified that he inappropriately touched them during class, pressed their hands to his genitals, and during piano lessons would alternate between having them sit on his lap while another played. Convicted of four counts of indecency with a child, sentenced to 80 years (four consecutive 20-year terms).",
        "crime": ["indecency with child"],
        "position": ["teacher", "piano instructor"],
        "tags": ["school predator", "child abuse", "Baptist school"]
    },
    946: {
        "name": "William Frank Brown",
        "year": 2009,
        "description": "William Frank Brown, 45, former pastor at Bellmead First Baptist Church in Waco, Texas, pled guilty to sexual assault of a minor between 2005 and 2007. He resigned just before police arrested him in April 2008. A grand jury indicted him in June 2008 on four counts of sexual assault of a child and four counts of indecency with a child. The victim disclosed abuse to a school counselor. Brown was sentenced to four concurrent 50-year prison sentences in 2009 and is not eligible for parole until after serving 25 years.",
        "crime": ["sexual assault", "indecency with child"],
        "position": ["pastor"],
        "tags": ["church abuse", "child abuse", "Baptist"]
    },
    947: {
        "name": "Benjamin Nelson",
        "year": 2017,
        "description": "Benjamin William Nelson, 28, pastor at Peoria Baptist Church in Hillsboro, Texas, was arrested February 27, 2017, for two counts of sexual assault of a child. Police found Nelson in a car with an underage girl at a Whitney shopping center. On March 2, 2017, Whitney Police added charges of indecency with a child and online solicitation of a minor. Nelson pleaded guilty to all five counts and was sentenced to 20 years in prison. He is required to register as a lifetime sex offender.",
        "crime": ["sexual assault", "indecency with child", "online solicitation"],
        "position": ["pastor"],
        "tags": ["church abuse", "child abuse", "Baptist"]
    },
    949: {
        "name": "Gary Don Welch",
        "year": 2012,
        "description": "Gary Don Welch, 42, minister of students at Northside Baptist Church in Corsicana, Texas, was arrested March 19, 2012, on charges of aggravated sexual assault of a child. A 16-year-old girl reported she had been sexually assaulted by Welch since 2009. He was indicted on one count of aggravated sexual assault, two counts of sexual assault of a child, and one count of indecency with a child. Convicted on all four counts, Welch received a 55-year prison sentence.",
        "crime": ["sexual assault", "indecency with child"],
        "position": ["youth minister"],
        "tags": ["church abuse", "child abuse", "Baptist"]
    },
    950: {
        "name": "Conner Jesse Penny",
        "year": None,
        "description": "Conner Jesse Penny is a youth pastor with criminal charges related to child abuse.",
        "crime": [],
        "position": ["youth pastor"],
        "tags": ["church abuse", "child abuse"]
    }
}

# Load enrichments
with open('/home/user/right-wing-predators/manual_enrichments.json', 'r', encoding='utf-8') as f:
    enrichments = json.load(f)

# Update matching entries
updated_count = 0
for entry in enrichments:
    if entry['id'] in updates:
        update_data = updates[entry['id']]
        for key, value in update_data.items():
            entry[key] = value
        updated_count += 1

# Save updated enrichments
with open('/home/user/right-wing-predators/manual_enrichments.json', 'w', encoding='utf-8') as f:
    json.dump(enrichments, f, indent=2, ensure_ascii=False)

print(f"Updated {updated_count} enrichments in batch 3 part 1")
