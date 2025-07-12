# How to Add GitHub Secrets

## Step-by-Step Instructions:

1. **Go to your repository**: 
   https://github.com/fieldjoshua/LightBox_2.0

2. **Click "Settings"** (it's in the top menu bar of your repo)
   ![Settings tab location]

3. **In the left sidebar, scroll down to "Security" section**

4. **Click on "Secrets and variables"** → **"Actions"**

5. **Click the green "New repository secret" button**

6. **Add each secret one by one:**

   ### Secret 1: PI_HOST
   - Name: `PI_HOST`
   - Value: `192.168.0.222`
   - Click "Add secret"

   ### Secret 2: PI_USER
   - Name: `PI_USER`
   - Value: `fieldjoshua`
   - Click "Add secret"

   ### Secret 3: PI_PASSWORD
   - Name: `PI_PASSWORD`
   - Value: (your raspberry pi password)
   - Click "Add secret"

   ### Secret 4: PI_PORT
   - Name: `PI_PORT`
   - Value: `22`
   - Click "Add secret"

## Visual Guide:

```
GitHub Repo → Settings → Secrets and variables → Actions → New repository secret
```

## Testing the Workflow:

After adding all secrets:

1. Go to the **"Actions"** tab in your repo
2. Click on "Sync to Raspberry Pi" workflow
3. Click "Run workflow" → "Run workflow" (green button)
4. Watch it sync!

## Security Note:

- These secrets are encrypted and only visible to GitHub Actions
- Never commit passwords or secrets directly in code
- You can update secrets anytime by clicking on them and updating

## Direct Link:

Try this direct link to your secrets page:
https://github.com/fieldjoshua/LightBox_2.0/settings/secrets/actions