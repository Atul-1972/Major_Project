"""Small lexical retrieval library of paraphrased, source-checked educational notes.

Reviewed 2026-10-29. No scraped pages, images or external retrieval requests at runtime.
These notes are not a comprehensive dermatology knowledge base or clinical validation.
"""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Note:
    id: str
    title: str
    url: str
    terms: str
    passage: str
    classes: tuple = ()


NOTES = (
    Note('anaphylaxis', 'NHS: Anaphylaxis', 'https://www.nhs.uk/conditions/anaphylaxis/',
         'allergy allergic breathing throat tongue swelling सांस गला सूजन saans',
         'A sudden serious allergic reaction can involve breathing difficulty or swelling of the tongue or throat. This requires immediate emergency medical help; online conversation must not delay care.'),
    Note('infection', 'NHS: Cellulitis', 'https://www.nhs.uk/conditions/cellulitis/',
         'infection hot swollen painful fever redness spreading बुखार दर्द गर्म sujan',
         'Painful, hot, swollen skin needs urgent clinical assessment. Fever or feeling very unwell can accompany a skin infection. Redness can be less obvious on darker skin. A chat or screening label cannot rule an infection in or out.'),
    Note('blistering', 'NHS: Stevens-Johnson syndrome', 'https://www.nhs.uk/conditions/stevens-johnson-syndrome/',
         'blister peeling mouth sores rash छाले त्वचा उतर मुंह',
         'A rapidly spreading painful rash with blistering, peeling skin, or mouth/eye involvement may indicate a serious reaction. Seek emergency medical assessment. Do not wait for an image prediction.'),
    Note('melanoma', 'AAD: ABCDEs of melanoma', 'https://www.aad.org/public/diseases/skin-cancer/abcdes-melanoma',
         'melanoma cancer asymmetry border color colour diameter evolving changing mole तिल बदल कैंसर',
         'Melanoma is a skin cancer. Warning signs include asymmetry, irregular borders, uneven colour and evolution over time. A changing, itching or bleeding spot should be examined by a dermatologist. The screening class is a possibility, not a diagnosis, and a low model score does not exclude cancer.', ('mel',)),
    Note('moles', 'NHS: Moles', 'https://www.nhs.uk/conditions/moles/',
         'mole moles nevus naevi melanocytic तिल',
         'Moles are pigmented skin spots that can be flat or raised. A change in size, shape or colour, itching, bleeding or crusting warrants medical review. A model label cannot establish whether an individual spot is benign.', ('nv',)),
    Note('actinic', 'NHS: Actinic keratoses', 'https://www.nhs.uk/conditions/actinic-keratoses/',
         'actinic keratosis keratoses sun scaly rough akiec धूप पपड़ी',
         'Actinic keratoses are rough patches associated with sun damage and can sometimes progress to skin cancer. The HAM10000 akiec category also includes intraepithelial carcinoma, so it must not be simplified to a harmless patch. A clinician must assess the actual lesion.', ('akiec',)),
    Note('bcc', 'AAD: Basal cell carcinoma', 'https://www.aad.org/public/diseases/skin-cancer/basal-cell-carcinoma',
         'basal cell carcinoma bcc sore cancer कैंसर घाव',
         'Basal cell carcinoma is a type of skin cancer. A persistent or recurring sore or changing growth needs dermatology evaluation. An AI screening output alone cannot confirm this condition or determine treatment.', ('bcc',)),
    Note('keratoses', 'AAD: Seborrheic keratoses', 'https://www.aad.org/public/diseases/a-z/seborrheic-keratoses-overview',
         'seborrheic seborrhoeic keratoses benign keratosis bkl',
         'Seborrheic keratoses are common skin growths that can resemble other lesions. The broad HAM10000 bkl class includes several keratosis-like diagnoses. An image label cannot identify the exact subtype or guarantee harmlessness; new or changing lesions need professional review.', ('bkl',)),
    Note('df', 'DermNet: Dermatofibroma', 'https://dermnetnz.org/topics/dermatofibroma',
         'dermatofibroma firm bump df गांठ',
         'A dermatofibroma is usually a firm skin nodule. Similar-looking lesions may need clinical examination to distinguish them. Do not identify a particular bump as benign from a screening score alone.', ('df',)),
    Note('vascular', 'DermNet: Cherry angioma', 'https://dermnetnz.org/topics/cherry-angioma',
         'vascular angioma hemangioma haemangioma vasc red purple रक्त',
         'Cherry angiomas are one example of blood-vessel-related skin growths. HAM10000 vasc is broader than this one condition. Do not infer a particular subtype from the class; changing or bleeding lesions merit clinical assessment.', ('vasc',)),
    Note('skin-care', 'AAD: Dry skin care', 'https://www.aad.org/public/everyday-care/skin-care-basics/dry/moisturize-dry-skin',
         'dry skin care gentle wash itchy moisturizer moisturiser sensitive खुजली सूखी त्वचा देखभाल khujli',
         'Gentle cleansing, avoiding irritating products, shorter warm rather than hot washes, and fragrance-free moisturising can support dry skin care. Persistent symptoms need assessment; these measures do not establish the cause of a rash or replace prescribed care.'),
)


def retrieve(message, prediction=None):
    tokens = set(re.findall(r'[\w\u0900-\u097f]+', message.casefold()))
    ranked = []
    code = prediction.get('code') if prediction else None
    for note in NOTES:
        score = len(tokens & set(note.terms.split())) + (20 if code in note.classes else 0)
        if score:
            ranked.append((score, note))
    ranked.sort(key=lambda item: -item[0])
    return [note for _, note in ranked[:3]] or [NOTES[-1]]


def sources(notes):
    return [{'id': note.id, 'title': note.title, 'url': note.url} for note in notes]
