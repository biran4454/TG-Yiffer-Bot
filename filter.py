import pygame
import os

# program shows image, user types y or n to indicate if the image should be kept, q to quit

def load_done():
    try:
        with open('done.txt') as f:
            return f.read().splitlines()
    except FileNotFoundError:
        print('No output file found, creating new one')
        open('done.txt', 'w').close()
        return []

def add_done(path):
    with open('done.txt', 'a') as f:
        f.write(path + '\n')

def run(photo_paths):
    SIZE = 600
    pygame.init()
    surface = pygame.display.set_mode((SIZE, SIZE))
    pygame.display.set_caption('Image Verification')
    
    i = 0
    prev = -1

    done = load_done()

    run = True
    while run:
        if i >= len(photo_paths):
            print('End of dataset')
            break
        if photo_paths[i] in done:
            i += 1
            continue

        if i != prev:
            surface.fill((0, 0, 0))
            image = pygame.image.load(photo_paths[i])
            image = pygame.transform.scale(image, (SIZE, image.get_height() * SIZE // image.get_width()))
            surface.blit(image, (0, 0))
            prev = i

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_y:
                    print(f'Keeping {photo_paths[i]}')
                    add_done(photo_paths[i])
                    i += 1
                    #os.rename(photo_paths[i], os.path.join('images\\accepted', os.path.basename(photo_paths[i])))
                    #photo_paths.pop(i)
                elif event.key == pygame.K_n:
                    print(f'Deleting {photo_paths[i]}')
                    os.remove(photo_paths[i])
                    photo_paths.pop(i)
                    prev = -1
                elif event.key == pygame.K_q:
                    run = False
                elif event.key == pygame.K_RIGHT:
                    if i < len(photo_paths) - 1:
                        i += 1
                elif event.key == pygame.K_LEFT:
                    if i > 0:
                        i -= 1

    pygame.quit()


if __name__ == '__main__':
    PATH = 'images'
    photo_paths = [os.path.join(PATH, f) for f in os.listdir(PATH) if f.endswith('.png') or f.endswith('.jpg')]
    run(photo_paths)