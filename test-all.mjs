import puppeteer from 'puppeteer-core';

const BASE = 'https://proletson.cn/meno';

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/google-chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-cache', '--disable-gpu']
  });

  const results = [];

  // ============ TEST 1: Login & check avatar ============
  console.log('=== TEST 1: Login & Avatar ===');
  const page1 = await browser.newPage();
  await page1.setViewport({ width: 390, height: 844 });
  await page1.setCacheEnabled(false);
  await page1.goto(BASE + '/?t=' + Date.now(), { waitUntil: 'domcontentloaded', timeout: 15000 });
  await new Promise(r => setTimeout(r, 2000));

  await page1.click('input[placeholder="请输入手机号"]');
  await page1.$eval('input[placeholder="请输入手机号"]', el => { el.value = ''; });
  await page1.type('input[placeholder="请输入手机号"]', '13712345678');
  const ci = await page1.$$('input[placeholder="验证码"]');
  await ci[0].click({ clickCount: 3 });
  await ci[0].type('1234');
  const lb = await page1.evaluateHandle(() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) if (b.textContent.includes('登录')) return b;
    return null;
  });
  await lb.click();
  await new Promise(r => setTimeout(r, 2000));

  // ============ TEST 2: Chat sends message and gets response ============
  await page1.evaluate(() => { document.querySelectorAll('.tab-item')[1]?.click(); });
  await new Promise(r => setTimeout(r, 1000));

  // Type a message asking about scale test results
  await page1.type('.chat-input-area input', '我最近的量表测试结果是什么？');
  await new Promise(r => setTimeout(r, 500));

  // Click send
  await page1.evaluate(() => {
    const btn = document.querySelector('.chat-input-area .el-button--primary');
    if (btn) btn.click();
  });

  // Wait for response (max 60s polling - LLM can be slow)
  let chatResponse = null;
  for (let i = 0; i < 60; i++) {
    await new Promise(r => setTimeout(r, 1000));
    chatResponse = await page1.evaluate(() => {
      const messages = document.querySelectorAll('.msg-row');
      const assistant = Array.from(messages).filter(m => m.classList.contains('assistant'));
      const lastAssistant = assistant[assistant.length - 1];
      // Skip "thinking" placeholder
      const bubble = lastAssistant?.querySelector('.msg-bubble');
      const text = bubble?.textContent?.trim() || '';
      if (text && text !== '正在思考...') {
        return {
          messageCount: messages.length,
          assistantCount: assistant.length,
          lastResponse: text.substring(0, 300),
        };
      }
      return null;
    });
    if (chatResponse) break;
  }
  chatResponse = chatResponse || await page1.evaluate(() => {
    const messages = document.querySelectorAll('.msg-row');
    const assistant = Array.from(messages).filter(m => m.classList.contains('assistant'));
    return {
      messageCount: messages.length,
      assistantCount: assistant.length,
      lastResponse: 'NO RESPONSE (timeout)',
    };
  });
  console.log('Chat:', JSON.stringify(chatResponse));
  results.push({ test: 'Chat gets response', pass: chatResponse.assistantCount > 0 && chatResponse.lastResponse !== 'NO RESPONSE (timeout)', detail: chatResponse });

  // ============ TEST 3: Chat response mentions scale data ============
  console.log('\n=== TEST 3: Scale data in AI response ===');
  const scaleMentioned = chatResponse.lastResponse && (
    chatResponse.lastResponse.includes('量表') ||
    chatResponse.lastResponse.includes('Kupperman') ||
    chatResponse.lastResponse.includes('荷尔蒙') ||
    chatResponse.lastResponse.includes('总分') ||
    chatResponse.lastResponse.includes('评估')
  );
  console.log('Scale data mentioned:', scaleMentioned);
  console.log('Response:', chatResponse.lastResponse);
  results.push({ test: 'AI can reference scale data', pass: scaleMentioned, detail: chatResponse.lastResponse });

  // ============ Check avatar in chat ============
  const avatarCheck = await page1.evaluate(() => {
    const userAvatar = document.querySelector('.msg-row.user .msg-avatar img');
    return {
      avatarSrc: userAvatar?.src || 'NOT FOUND',
      avatarLoaded: userAvatar?.complete && userAvatar?.naturalWidth > 0,
    };
  });
  console.log('Avatar:', JSON.stringify(avatarCheck));
  results.push({ test: 'Avatar loads', pass: avatarCheck.avatarSrc !== 'NOT FOUND', detail: avatarCheck });

  // ============ TEST 4: Backstage login ============
  console.log('\n=== TEST 4: Backstage Login ===');
  const page2 = await browser.newPage();
  await page2.setCacheEnabled(false);
  await page2.goto(BASE + '/backstage/login?t=' + Date.now(), { waitUntil: 'domcontentloaded', timeout: 15000 });
  await new Promise(r => setTimeout(r, 2000));

  const backstageLogin = await page2.evaluate(() => {
    const input = document.querySelector('input[type="password"]');
    const btn = document.querySelector('button[type="submit"], .btn');
    return { hasLogin: !!input, hasBtn: !!btn };
  });
  console.log('Backstage login page:', JSON.stringify(backstageLogin));
  results.push({ test: 'Backstage login page loads', pass: backstageLogin.hasLogin, detail: backstageLogin });

  // Login
  await page2.type('input[type="password"]', 'admin123');
  await page2.evaluate(() => {
    const btn = document.querySelector('button[type="submit"], .btn');
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 3000));

  const backstageDashboard = await page2.evaluate(() => {
    const cards = document.querySelectorAll('.stat-card');
    const values = Array.from(cards).map(c => ({
      label: c.querySelector('.stat-label')?.textContent?.trim(),
      value: c.querySelector('.stat-value')?.textContent?.trim(),
    }));
    return {
      url: window.location.pathname,
      statCards: values,
    };
  });
  console.log('Backstage dashboard:', JSON.stringify(backstageDashboard));
  results.push({ test: 'Backstage dashboard shows real data', pass: backstageDashboard.statCards.length > 0, detail: backstageDashboard });

  // ============ TEST 5: Backstage user list ============
  console.log('\n=== TEST 5: Backstage User List ===');
  await page2.goto(BASE + '/backstage/users?t=' + Date.now(), { waitUntil: 'domcontentloaded', timeout: 15000 });
  await new Promise(r => setTimeout(r, 3000));

  const userList = await page2.evaluate(() => {
    const rows = document.querySelectorAll('table tbody tr');
    const users = Array.from(rows).map(row => {
      const cells = row.querySelectorAll('td');
      return {
        name: cells[0]?.textContent?.trim(),
        phone: cells[1]?.textContent?.trim(),
      };
    });
    return {
      userCount: rows.length,
      users: users,
    };
  });
  console.log('User list:', JSON.stringify(userList));
  results.push({ test: 'Backstage shows real users', pass: userList.userCount > 0, detail: userList });

  // ============ TEST 6: Backstage user detail ============
  console.log('\n=== TEST 6: Backstage User Detail ===');
  if (userList.userCount > 0) {
    // Navigate directly to the user detail page
    const userId = await page2.evaluate(() => {
      const link = document.querySelector('table tbody tr a');
      return link ? link.href.split('/').pop() : null;
    });
    if (userId) {
      await page2.goto(BASE + `/backstage/users/${userId}?t=` + Date.now(), { waitUntil: 'domcontentloaded', timeout: 15000 });
      await new Promise(r => setTimeout(r, 2000));

      const userDetail = await page2.evaluate(() => {
        const cards = document.querySelectorAll('.card');
        const cardTitles = Array.from(cards).map(c => c.querySelector('.card-title')?.textContent?.trim());
        return { url: window.location.pathname, cards: cardTitles };
      });
      console.log('User detail:', JSON.stringify(userDetail));
      results.push({ test: 'User detail page loads', pass: userDetail.cards.length > 0, detail: userDetail });
    }
  }

  // ============ SUMMARY ============
  console.log('\n========== SUMMARY ==========');
  let passed = 0;
  for (const r of results) {
    const status = r.pass ? 'PASS' : 'FAIL';
    console.log(`[${status}] ${r.test}`);
    if (!r.pass) console.log(`   Detail: ${JSON.stringify(r.detail)}`);
    if (r.pass) passed++;
  }
  console.log(`\n${passed}/${results.length} tests passed`);

  await browser.close();
})();
