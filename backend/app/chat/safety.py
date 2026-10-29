"""Conservative bilingual input triage and output checks; not clinical validation."""

import re
import unicodedata


def normalize(message):
    return unicodedata.normalize('NFKC', message).casefold()


def positive_match(pattern, message):
    for match in re.finditer(pattern, message):
        prefix = re.split(r'[.!?;,]|\bbut\b|\bhowever\b|लेकिन', message[:match.start()])[-1]
        if re.search(r'\b(no|not|without|deny|denies)\s+(?:\w+\s+){0,2}$', prefix):
            continue
        if re.match(r'.{0,10}(नहीं|नही)', message[match.end():]):
            continue
        return True
    return False


def triage(message):
    value = normalize(message)
    emergency = (
        r"(?:difficulty|trouble|struggling|cannot|can't|unable).{0,12}breath\w*",
        r'short(?:ness)? of breath|throat.{0,10}tight|difficulty swallowing',
        r'(?:throat|tongue|lips).{0,18}(?:swell\w*|swollen)',
        r'(?:swollen|swelling).{0,18}(?:throat|tongue|lips)',
        r'(?:widespread|severe).{0,12}blister\w*|skin.{0,10}peeling',
        r'सांस लेने में (?:दिक्कत|कठिनाई|परेशानी)|साँस लेने में (?:दिक्कत|कठिनाई)|(?:गले|जीभ).{0,15}सूजन',
        r'saans.{0,16}(?:dikkat|mushkil)|gale.{0,12}sujan',
        r'(?:सांस|साँस).{0,8}(?:नहीं|नही).{0,8}(?:आ|ले)',
    )
    if any(positive_match(pattern, value) for pattern in emergency) or 'saans nahi aa' in value:
        return 'emergency'
    signs = [positive_match(pattern, value) for pattern in
             (r'fever|बुखार|bukhar', r'painful|severe pain|दर्द|dard',
              r'hot|warm|गर्म', r'swell\w*|swollen|सूजन|sujan', r'spread\w*|फैल')]
    if (signs[0] and any(signs[1:])) or sum(signs[1:4]) >= 3:
        return 'urgent'
    return None


def safety_reply(level, language):
    if language == 'hi':
        if level == 'emergency':
            return 'ये लक्षण गंभीर हो सकते हैं। अभी स्थानीय आपातकालीन सेवा से संपर्क करें या नज़दीकी आपातकालीन विभाग जाएँ। चैट या त्वचा की AI रिपोर्ट के लिए प्रतीक्षा न करें। मैं निदान नहीं कर सकता।'
        return 'इन लक्षणों के लिए आज ही चिकित्सक से तुरंत जाँच करवाएँ। यदि साँस लेने में कठिनाई, बेहोशी या तेज़ बिगड़ाव हो तो आपातकालीन सहायता लें। AI रिपोर्ट किसी गंभीर समस्या को नकार नहीं सकती।'
    if level == 'emergency':
        return 'These symptoms may be serious. Contact local emergency services or go to the nearest emergency department now. Do not wait for this chat or an AI skin result. I cannot diagnose the cause.'
    return 'Please seek urgent in-person medical assessment today. If breathing difficulty, fainting or rapid deterioration occurs, seek emergency help now. An AI skin result cannot rule out a serious problem.'


def unsafe_output(text):
    value = normalize(text)
    patterns = (
        r'\b\d+(?:\.\d+)?\s*(?:mg|mcg|milligram|tablets?|capsules?)\b',
        r'\b(?:take|apply|start|use)\b.{0,65}\b(?:steroid|antibiotic|hydrocortisone|clobetasol|isotretinoin|cream|ointment|medicine|medication)\b',
        r'\byou (?:definitely |certainly )?have\b|\bconfirmed diagnosis\b',
        r'\b(?:harmless|guaranteed safe|not cancer|no need to see|nothing to worry|100% safe)\b',
        r'(?:कैंसर नहीं|बिल्कुल सुरक्षित|पक्का निदान|दवा लें|दवाई लें|क्रीम लगाएं|क्रीम लगाएँ|खतरा नहीं)',
        r'https?://|www\.',
    )
    return any(re.search(pattern, value) for pattern in patterns)


def blocked_reply(language):
    if language == 'hi':
        return 'मैं पक्का निदान, दवा या खुराक नहीं बता सकता। त्वचा की समस्या के लिए योग्य त्वचा रोग विशेषज्ञ से जाँच करवाएँ। समस्या कब से है, और क्या खुजली, दर्द या आकार/रंग में बदलाव हुआ है?'
    return 'I cannot confirm a diagnosis, prescribe medicines or recommend a dose. A qualified dermatologist can assess the skin concern. How long has it been present, and has there been itching, pain, or a change in size or colour?'
