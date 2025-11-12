// api/proxy.js (JavaScript - Vercel Serverless Function)

const TARGET_URL = 'http://noel.hidencloud.com:24674/webhook';

// هذه الدالة ستستقبل كل الطلبات الواردة من فيسبوك
export default async (req, res) => {
  try {
    // 1. معالجة طلب التحقق (GET Request)
    if (req.method === 'GET') {
      // يجب أن نمرر رمز التحقق الخاص بك (boykta20071408)
      const verifyToken = 'boykta20071408';

      const mode = req.query['hub.mode'];
      const token = req.query['hub.verify_token'];
      const challenge = req.query['hub.challenge'];

      if (mode === 'subscribe' && token === verifyToken) {
        // التحقق نجح: إرجاع الرمز (Challenge)
        console.log("Verification Success!");
        return res.status(200).send(challenge);
      } else {
        console.error("Verification failed: Token mismatch.");
        return res.status(403).send('Invalid verification token');
      }
    }

    // 2. معالجة الرسائل والبيانات (POST Request)
    else if (req.method === 'POST') {
      // إعادة توجيه طلب الـ POST بالكامل إلى خادم Python
      const response = await fetch(TARGET_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body) 
      });

      // إرجاع استجابة خادم Python (عادةً 200 OK)
      return res.status(response.status).send('OK');
    }

    return res.status(405).send('Method Not Allowed');

  } catch (error) {
    console.error('Proxy Error:', error);
    return res.status(500).send('Proxy failure');
  }
};
