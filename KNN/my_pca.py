

#Import the required libraries
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
import pandas as pd


#Main function to apply PCA algorithm
def my_pca(data, img_w, img_h, train_labels, test_data, test_labels, training_phase, N, goal_variance, show_plot, show_comparison):

    data = np.transpose(data)

    #3 I apply PCA and project the train images into a space of dimension N

    # 3a. I calculate the mean and centre the data
    m = np.mean(data, axis=1)     #for every pixel (i,j) mean between all the images pixels (es: 256,)
    Xc = data - m[:, np.newaxis]  #centralized coordinates over "m"

    # 3b. I calculate the covariance matrix
    C = np.cov(Xc)

    # 3c. Extracting eigenvectors and eigenvalues of the covariance matrix
    lambdas, U = np.linalg.eigh(C)

    # 3d. I order the eigenvalues from largest to smallest
    best_eig_idxs = np.argsort(lambdas)[::-1]  #ascending sort that is then reversed to achieve descending sorting
                                               #argsort returns indeces
    best_eig = lambdas[best_eig_idxs]  #get the "highest" eigenvalues
    best_U = U[:, best_eig_idxs]       #get the associated eigenvectors to their eigenvalues

    # 3e. I check the amount of variance in the data that each eigenvalue carries and set N equal to the number of eigenvectors sufficient to have at least 80%
    # of the total variance.
    d = lambdas.shape[0]  #number of eigenvalues

    if training_phase:
        y = np.cumsum(best_eig) / np.sum(best_eig)  # normalize eigenvalues between 0 and 1 (0= the most significative)
        if show_plot:
            fig, axs = plt.subplots(2)
            axs[0].plot(np.arange(1, d + 1), best_eig)  # draw the line (xlimit = [1,256])
            axs[0].scatter(np.arange(1, d + 1), best_eig)  # scatter the eigenvalues points
            axs[1].plot(np.arange(1, d + 1), y)  # draw the line (xlimit = [1,256])
            axs[1].scatter(np.arange(1, d + 1), y)  # scatter the values
            plt.show()

        N = np.where(y >= goal_variance)[0][0]  #get the first ("0") element that satisfies y>=...
        if show_comparison:
            print("[myPCA] From PCA (implemented step by step) we get that the number of components to have",
                   str(np.round(goal_variance, 2)), "explained variance is", N)

    # 3f. I project the data using the N largest eigenvectors
    first_N_eigenvectors = best_U[:, :N]   #get the first N more significant eigenvectors (previously ordered)
    projectedImages = first_N_eigenvectors.T.dot(Xc)

    if training_phase:
        # Computing the accuracy achieved by the PCA classifier
        accuracy = test_my_pca(first_N_eigenvectors, projectedImages, train_labels, test_data, test_labels, m, show_updates=show_comparison)
        return np.transpose(projectedImages), N, accuracy
    else:
        return np.transpose(projectedImages)

#Function that prints the accuracy of the PCA feature reduction
def test_my_pca(first_N_eigenvectors, projected_images, train_labels, test_data, test_labels, m, show_updates):
    # 4. Calculating the Theta threshold
    from scipy.spatial.distance import cdist
    theta = np.max(cdist(projected_images.T, projected_images.T, 'euclidean'))

    # 5. Centre my test data
    test_data = np.transpose(test_data)  #to match sizes (similar to the training data)

    x_te = test_data - m[:, np.newaxis]

    omega_te = first_N_eigenvectors.T.dot(x_te)

    # 6. Calculating the set of epsilon distances
    epsilon = []
    for i in range(test_data.shape[1]):
        tmp_test = omega_te[:, i]
        epsilon.append(np.linalg.norm(tmp_test[:, np.newaxis] - projected_images, ord=2, axis=0))

    epsilon = np.array(epsilon)

    # 7. I reconstruct the images and make an imshow of the original against the reconstructed one in the first 5 images!
    g = first_N_eigenvectors.dot(omega_te)
    '''
    fig, axs = plt.subplots(5, 2)
    for i in range(5):
        axs[i, 0].imshow(x_te[:, i].reshape((r, c)), cmap='gray')
        axs[i, 1].imshow(g[:, i].reshape((r, c)), cmap='gray')
    plt.show()
    '''

    # 8. Calculation xi for classification
    xi = np.linalg.norm(g - x_te, ord=2, axis=0)

    # 9. In which of the 3 cases are we for each test image? Is the corresponding image of the same class? Check the first 5 images
    ''' # It does not work in our case, because Xc variable is defined out of scope of this function
    fig, axs = plt.subplots(5, 2)
    for i in range(5):
        if xi[i] >= theta:
            print(str(i + 1) + ": It's not one of the classes!")
        elif xi[i] < theta and any(epsilon[i, :] > theta):
            print(str(i + 1) + ": It's a new image of one of the classes!")
        elif xi[i] < theta and np.min(epsilon[i, :]) < theta:
            print(str(i + 1) + ": It's a familiar image! I'll show you!")
            matched_indx = np.argmin(epsilon[i, :])
            axs[i, 0].imshow(x_te[:, i].reshape((r, c)), cmap='gray')
            axs[i, 1].imshow(Xc[:, matched_indx].reshape((r, c)), cmap='gray')
            if i == 0:
                axs[i, 0].set_title('Unknown class!')
                axs[i, 1].set_title('Known class!')
    plt.show()
    '''

    # 10. Calculate the accuracy of the classifier and test how the result changes when N (+/- eigenvectors) is changed
    # Set the prediction equal to -1 in case of classification as no one of the classes or new image of one of the 6 classes,
    # equal to the train sample label with lower epsilon if a match is found
    predicted = []
    for i in range(test_data.shape[1]):
        if xi[i] < theta and np.min(epsilon[i, :]) < theta:
            predicted.append(train_labels[np.argmin(epsilon[i, :])])
        else:
            predicted.append(-1)

    predicted = np.array(predicted)

    accuracy = np.sum(predicted == test_labels)
    if show_updates:
        print('[myPCA] Classifier accuracy: ' + "{0:.2f}".format(accuracy / len(test_labels) * 100) + '%\n')
    return accuracy / len(test_labels) * 100



def my_pca_tuning(increment_range, increment, imageSize, trainImages, trainLabels, testImages, testLabels, show_updates, featureType):
    startingVariance = increment_range[0]
    finalVariance = increment_range[1]
    actualVariance = startingVariance
    bestGoalVariance = 0
    bestAccuracy = 0
    allAccuracies = []

    while actualVariance < finalVariance:
        if show_updates:
            print("[PCA tuning] Considering variance=" + str(np.round(actualVariance, 2)))

        _, N, accuracy = my_pca(trainImages, imageSize, imageSize, trainLabels, testImages, testLabels,
                                training_phase=True, N=None, goal_variance=actualVariance, show_plot=False,
                                show_comparison=show_updates)  #reducing feature space

        allAccuracies.append(accuracy)  #save the current accuracy to then create a csv file

        if accuracy > bestAccuracy:
            bestAccuracy = accuracy
            bestGoalVariance = actualVariance
            N_best = N

        actualVariance += increment

    cols = np.arange(0.6, 0.9, 0.05)
    df = pd.DataFrame([allAccuracies], columns=cols)
    df.to_csv('csvLogs/PCA_accuracy_'+featureType+'.csv', index=False)

    return bestGoalVariance, bestAccuracy, N_best


def sklearn_pca(features, goalVariance):

    scaler = MinMaxScaler()
    scaledFeatures = scaler.fit_transform(features)

    pca = PCA(n_components=goalVariance)
    pca.fit_transform(scaledFeatures)

    print("[sklearn PCA] PCA components considering the set variance ratio (" + str(np.round(goalVariance, 2)) + "): "
          + str(pca.explained_variance_ratio_.shape[0]))
